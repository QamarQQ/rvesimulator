#                                                                       Modules
# =============================================================================
# Third party
import numpy

# abaqus
from abaqus import *
from abaqusConstants import *
from caeModules import *

#                                                          Authorship & Credits
# =============================================================================
__author__ = "Jiaxiang Yi (J.Yi@tudelft.nl)"
__credits__ = ["Jiaxiang Yi"]
__status__ = "Alpha"
# =============================================================================
#
# =============================================================================


class Loading2D:
    def __init__(self, model, assembly, instance_name):
        """initialization of loadings

        Parameters
        ----------
        model : abaqus model
            abaqus model
        assembly : assembly
            abaqus assembly
        instance_name : instance
            abaqus instance
        """
        self.model = model
        self.assembly = assembly
        self.instance = instance_name

    def create_loads(self, loads):
        # loads should be a list with three elemnts

        E11 = loads[0]
        E22 = loads[1]
        E12 = loads[2]

        self.model.DisplacementBC(
            name="E_11",
            createStepName="Step-1",
            region=self.assembly.sets["Ref-R"],
            u1=E11,
            u2=UNSET,
            ur3=UNSET,
            amplitude=UNSET,
            fixed=OFF,
            distributionType=UNIFORM,
            fieldName="",
            localCsys=None,
        )

        self.model.DisplacementBC(
            name="E_22",
            createStepName="Step-1",
            region=self.assembly.sets["Ref-T"],
            u1=UNSET,
            u2=E22,
            ur3=UNSET,
            amplitude=UNSET,
            fixed=OFF,
            distributionType=UNIFORM,
            fieldName="",
            localCsys=None,
        )

        self.model.DisplacementBC(
            name="E_12",
            createStepName="Step-1",
            region=self.assembly.sets["Ref-R"],
            u1=UNSET,
            u2=E12,
            ur3=UNSET,
            amplitude=UNSET,
            fixed=OFF,
            distributionType=UNIFORM,
            fieldName="",
            localCsys=None,
        )
        self.model.DisplacementBC(
            name="E_21",
            createStepName="Step-1",
            region=self.assembly.sets["Ref-T"],
            u1=E12,
            u2=UNSET,
            ur3=UNSET,
            amplitude=UNSET,
            fixed=OFF,
            distributionType=UNIFORM,
            fieldName="",
            localCsys=None,
        )

    def create_path_load(self, load_magnitude, path_table, time_period):
        """create path loads

        Parameters
        ----------
        load_magnitude : list
            loads magitude, such as [0.02, 0.02,0.02]
        path_table : list
            the exact path
        time_period : float
            simulation time
        """
        # loads should be a list with three elemnts
        E11 = load_magnitude[0]
        E22 = load_magnitude[1]
        E12 = load_magnitude[2]
        num_point = path_table.shape[0]
        # create the path amplitude first
        path_name = ["xx", "yy", "xy"]
        for ii, name in enumerate(path_name):
            path_table_temp = numpy.zeros((num_point, 2))
            path_table_temp[:, 0] = numpy.linspace(
                0, time_period, num_point, endpoint=True
            )
            path_table_temp[:, 1] = path_table[:, ii]
            self._create_random_path(path_table_temp, name)

        # create load for corresonding part
        # create E_11
        self.model.DisplacementBC(
            name="E11",
            createStepName="Step-1",
            region=self.assembly.sets["Ref-R"],
            u1=E11,
            u2=UNSET,
            ur3=UNSET,
            amplitude=path_name[0],
            fixed=OFF,
            distributionType=UNIFORM,
            fieldName="",
            localCsys=None,
        )
        # create E_22
        self.model.DisplacementBC(
            name="E22",
            createStepName="Step-1",
            region=self.assembly.sets["Ref-T"],
            u1=UNSET,
            u2=E22,
            ur3=UNSET,
            amplitude=path_name[1],
            fixed=OFF,
            distributionType=UNIFORM,
            fieldName="",
            localCsys=None,
        )
        # create E_12
        self.model.DisplacementBC(
            name="E12",
            createStepName="Step-1",
            region=self.assembly.sets["Ref-R"],
            u1=UNSET,
            u2=E12,
            ur3=UNSET,
            amplitude=path_name[2],
            fixed=OFF,
            distributionType=UNIFORM,
            fieldName="",
            localCsys=None,
        )
        # create E_21
        self.model.DisplacementBC(
            name="E21",
            createStepName="Step-1",
            region=self.assembly.sets["Ref-T"],
            u1=E12,
            u2=UNSET,
            ur3=UNSET,
            amplitude=path_name[2],
            fixed=OFF,
            distributionType=UNIFORM,
            fieldName="",
            localCsys=None,
        )

    def _create_random_path(self, path_tale, path_name):

        # generate the table
        self.model.TabularAmplitude(
            name=path_name,
            timeSpan=TOTAL,
            smooth=SOLVER_DEFAULT,
            data=(path_tale),
        )