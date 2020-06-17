from maya.api import OpenMaya as om


class Component(tuple):
    """
        This class groups component information as a 3-tuple: weight index (int), component
        name (str), and indices (tuple of int).

        Example:
            comp = Component( (51, 'vtx[51]', (51,)) )
            comp = Component( (32, 'cv[10][2], (10, 2)) )

        The weight index is a single index that matches the index of array attributes
        that store per-component information, such as shape.controlPoints or
        deformer.weightList.weights. For periodic a nurbsSurface this index is sparse,
        as the overlapping CVs are hidden.

        The component evaluates as a string for comparison and hash table look-up. This
        allows you to find it in a dictionary using the name only, rather than having
        to use the Component object.

        Example:
            comp = Component( (51, 'vtx[51]', (51,)) )
            comp == 'vtx[51]'
            # Result: True #

            'bodySubD.{0}'.format(comp)
            # Result: 'bodySubD.vtx[51]' #

            comp_positions = {comp: (1, 2, 3)}
            comp_positions['vtx[51]']
            # Result: (1, 2, 3) #

            comp_positions[comp]
            # Result: (1, 2, 3) #
        """

    @classmethod
    def deserialize(cls, data):
        """
        Returns a component from the serialized data.
        Args:
            data (list): weight index (int), name (str), indices (list)
        Returns:
            Component: component
        """
        return cls(data)

    def __str__(self):
        """
        Returns the component as a string, allowing you to use the component in string
        formatting.
        Returns:
            str: string representation of the component name
        """
        return str(self[1])

    def __repr__(self):
        """
        Returns a machine readable string representation (e.g. Component(6, 'vtx[6]', (6,))).
        Returns:
            str: list representation of the component name
        """
        return '{0}{1}'.format(self.__class__.__name__, tuple(self))

    def __hash__(self):
        """
        Returns the hash code generated from the component name, allowing you to
        add the component to a set or use as dictionary key.
        Returns:
            int: hash code of the component name
        """
        return hash(self[1])

    @property
    def indices(self):
        """
        The indices of the component. The number of indices depends on the type of
        component.
        Returns:
            tuple: component indices as tuple of int
        """
        return self[2]

    @property
    def weight_index(self):
        """
        The weight index is a single index that matches the index of array attributes that store
        per-component information, such as shape.controlPoints or deformer.weightList.weights.
        For periodic a nurbsSurfaces this index is sparse, as the overlapping CVs are hidden.
        Returns:
            int: weight index of the component
        """
        return self[0]

    def serialize(self):
        """
        Returns serialized data for the component.
        Returns:
            tuple: weight index (int), name (str), indices (list)
        """
        return tuple(self)


class Components(set):

    @classmethod
    def from_curve_cvs(cls, curve, hidden=False):
        """
        Returns components from all the CVs of the given nurbsCurve.
        Args:
            curve (str): nurbsCurve
            hidden (bool): True returns hidden (overlapping) cvs
        Returns:
            Components: set of CVs
        """
        curve_fn = om.MFnNurbsCurve()
        curve_fn.setObject(om.MGlobal.getSelectionListByName(curve).getDagPath(0))
        num_cvs = (curve_fn.numCVs - curve_fn.degree if curve_fn.form == curve_fn.kPeriodic and not hidden
                   else curve_fn.numCVs)
        return cls(Component((i, 'cv[%s]' % i, (i,))) for i in xrange(num_cvs))

    def __init__(self, *args, **kwargs):
        """ Initializes a new instance of component list. """
        super(Components, self).__init__(*args, **kwargs)
        self._component_dict = None
