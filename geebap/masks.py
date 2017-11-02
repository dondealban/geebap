# -*- coding: utf-8 -*-
""" Modulo que contiene las clases para las mascaras a aplicar en la generacion
del compuesto BAP """

import satcol
import ee
from abc import ABCMeta, abstractmethod

class Mascara(object):
    __metaclass__ = ABCMeta
    """ Clase base para las mascaras """
    def __init__(self, nombre="masks", **kwargs):
        self.nombre = nombre

    @abstractmethod
    def map(self, **kwargs):
        pass

class Manual(object):
    pass

class Nubes(Mascara):
    """ Mascara de nubes propia de la coleccion """
    def __init__(self, **kwargs):
        super(Nubes, self).__init__(**kwargs)
        self.nombre = "nubes"

    def map(self, col, **kwargs):
        """
        :param col: Coleccion
        :type col: satcol.Coleccion
        :param kwargs:
        :return: la funcion para enmascarar la/s imagen/es con la mascara de
            nubes que indica el objeto Coleccion
        :rtype: function
        """
        if col.fnubes:
            return col.fnubes
        else:
            return lambda x: x


class Equivalente(Mascara):
    """ Enmascara las nubes de una imagen LEDAPS utilizando la misma imagen
    de la coleccion TOA.

    :Parametros:

    :param fechafld: propiedad de la imagen en la que está alojada la fecha de
        la misma (DATE_ACQUIRED)
    :type fechafld: str

    :param fld: banda de la imagen en la que está el valor de fmask (fmask)
    :type fld: str

    :param col: colección que se quiere enmascarar STRING (argumento)
        EJ: 'LEDAPS/LT5_L1T_SR'
    :type col: str
    """

    def __init__(self, **kwargs):
        super(Equivalente, self).__init__(**kwargs)
        self.nombre = "equivalente"

    def map(self, col, **kwargs):
        """
        Propósito: para usar en la función map() de GEE
        Objetivo: enmascara en cada imagen de la coleccion la sombra de la nube
        Devuelve: la propia imagen enmascarada
        :param col: Coleccion
        :type col: satcol.Coleccion
        """
        fam = col.familia
        tipo = col.proceso
        equivID = col.equiv

        # if fam == "Landsat" and tipo == "SR" and (colequiv is not None):
        if equivID:
            colequiv = satcol.Coleccion.from_id(equivID)
            mask = colequiv.nubesBand
            def wrap(img):
                path = img.get("WRS_PATH")
                row = img.get("WRS_ROW")
                # TODO: usar un filtro de EE (ee.Filter)
                dateadq = ee.Date(img.date())
                nextday = dateadq.advance(1, "day")

                filtered = (colequiv.colEE
                .filterMetadata("WRS_PATH", "equals", path)
                .filterMetadata("WRS_ROW", "equals", row)
                .filterDate(dateadq, nextday))

                # TOA = ee.Image(filtered.first())
                newimg = ee.Algorithms.If(
                    filtered.size(),
                    img.updateMask(ee.Image(filtered.first()).select(mask).neq(2)),
                    img)

                # fmask = TOA.select(mask)
                # mascara = fmask.eq(2)
                #return img.updateMask(mascara.Not())
                return ee.Image(newimg)
                ## return img
        else:
            def wrap(img): return img

        return wrap