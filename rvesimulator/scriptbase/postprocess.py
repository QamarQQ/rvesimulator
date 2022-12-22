# abaqus
# import python libraries
import numpy
from abaqus import *
from abaqusConstants import *
from caeModules import *
from odbAccess import *

try:
    import cPickle as pickle  # Improve speed
except ValueError:
    import pickle

class RVEPostProcess(object):

    def __init__(self, job_name):
        self.job_name = job_name
        self._rve_results()

    def _element_set(self, RVEodb):
        """
        choose corresponding element set for the post analysis

        Parameters
        ----------
        RVEodb: The odb file generated after the Abaqus simulation

        Returns
        -------
        entireRVE_elSet: the selected element set of analysis

        """
        if self.job_name == 'HollowPlateRVE':
            entireRVE_elSet = RVEodb.rootAssembly.elementSets[' ALL ELEMENTS']
        elif self.job_name == 'ASCARVE':
            entireRVE_elSet = RVEodb.rootAssembly.instances['FINAL_STUFF'].elementSets['MATRIXFACE']
        elif self.job_name == 'PPandPEComposie':
            entireRVE_elSet = RVEodb.rootAssembly.elementSets[' ALL ELEMENTS']
        else:
            print('The job name is not defined in the default setting !\n')

        return entireRVE_elSet

    def _rve_results(self):

        ## basic information of the odb file
        # Define the name of the Phase_1 part
        odbfile = self.job_name + '.odb'  # Define name of this .odb file
        RVEodb = openOdb(path=odbfile)
        # Determine the number of steps in the output database.
        mySteps = RVEodb.steps
        numSteps = len(mySteps)

        entireRVE_elSet = self._element_set(RVEodb=RVEodb)

        dummy1_nSet = RVEodb.rootAssembly.nodeSets['REF-R']
        dummy2_nSet = RVEodb.rootAssembly.nodeSets['REF-T']
        #
        # For each step, obtain the following:
        #     1) The step key.
        #     2) The number of frames in the step.
        #     3) The increment number of the last frame in the step.
        #
        totalNumFrames = 0
        for iStep in range(numSteps):
            stepKey = mySteps.keys()[iStep]
            step = mySteps[stepKey]
            numFrames = len(step.frames)
            totalNumFrames = totalNumFrames + numFrames

        # Preallocate quantities for speed
        RVEframe = RVEodb.steps[mySteps.keys()[0]].frames[0]  # Undeformed config.
        # Extract volume at integration point in ENTIRE RVE:
        ivolField = RVEframe.fieldOutputs['IVOL']
        ivolSubField = ivolField.getSubset(region=entireRVE_elSet, position=INTEGRATION_POINT)
        ivol = numpy.zeros((len(ivolSubField.values)))
        # stress = numpy.zeros((len(ivolSubField.values)))
        tot_vol = 0.0
        for i in range(0, len(ivolSubField.values)):
            ivol[i] = ivolSubField.values[i].data  # Volume for i-th integration point
            tot_vol = tot_vol + ivol[i]  # total volume

        # finished computing volume at integration points and total volume
        U_Field = RVEframe.fieldOutputs['U']
        U_dummy1_SubField = U_Field.getSubset(region=dummy1_nSet, position=NODAL)
        U_dummy2_SubField = U_Field.getSubset(region=dummy2_nSet, position=NODAL)
        #
        if isinstance(U_dummy1_SubField.values[0].data, float):
            # Then variable is a scalar
            U_dummy1 = numpy.zeros((totalNumFrames))
            U_dummy2 = numpy.zeros((totalNumFrames))
        else:
            # Variable is an array
            U_dummy1 = numpy.zeros((totalNumFrames, len(U_dummy1_SubField.values[0].data)))
            U_dummy2 = numpy.zeros((totalNumFrames, len(U_dummy2_SubField.values[0].data)))

        RF_Field = RVEframe.fieldOutputs['RF']
        RF_dummy1_SubField = RF_Field.getSubset(region=dummy1_nSet, position=NODAL)
        RF_dummy2_SubField = RF_Field.getSubset(region=dummy2_nSet, position=NODAL)

        #
        if isinstance(RF_dummy1_SubField.values[0].data, float):
            # Then variable is a scalar
            RF_dummy1 = numpy.zeros((totalNumFrames))
            RF_dummy2 = numpy.zeros((totalNumFrames))
        else:
            # Variable is an array
            RF_dummy1 = numpy.zeros((totalNumFrames, len(RF_dummy1_SubField.values[0].data)))
            RF_dummy2 = numpy.zeros((totalNumFrames, len(RF_dummy2_SubField.values[0].data)))

        # Loop over Steps and Frames to compute average quantities in RVE
        eye = numpy.identity(2)
        defGrad = numpy.zeros((totalNumFrames, 2, 2))
        nomP = numpy.zeros((totalNumFrames, 2, 2))
        jacobian = numpy.zeros(totalNumFrames)
        Green_strain = numpy.zeros((totalNumFrames, 2, 2))
        PK2 = numpy.zeros((totalNumFrames, 2, 2))
        stepTotalTime = numpy.zeros(numSteps)
        previousFrame = 0
        numFrames = 0
        for iStep in range(numSteps):
            previousFrame = previousFrame + numFrames
            stepKey = mySteps.keys()[iStep]
            step = mySteps[stepKey]
            stepTotalTime[iStep] = step.timePeriod
            numFrames = len(step.frames)
            #
            for iFrame_step in range(0, numFrames):
                iFrame = previousFrame + iFrame_step
                RVEframe = RVEodb.steps[stepKey].frames[iFrame]
                # Finished computing average for this variable!
                # Variable: U
                U_Field = RVEframe.fieldOutputs['U']
                U_dummy1_SubField = U_Field.getSubset(region=dummy1_nSet, position=NODAL)
                U_dummy2_SubField = U_Field.getSubset(region=dummy2_nSet, position=NODAL)
                #
                if isinstance(U_dummy1_SubField.values[0].data, float):
                    # Then variable is a scalar:
                    U_dummy1[iFrame] = U_dummy1_SubField.values[0].data
                    U_dummy2[iFrame] = U_dummy2_SubField.values[0].data
                    #
                else:
                    # Variable is an array:
                    for j in range(0, len(U_dummy1_SubField.values[0].data)):
                        U_dummy1[iFrame][j] = U_dummy1_SubField.values[0].data[j]
                        U_dummy2[iFrame][j] = U_dummy2_SubField.values[0].data[j]

                # Finished saving this variable at the dummy nodes!
                # Variable: RF
                RF_Field = RVEframe.fieldOutputs['RF']
                RF_dummy1_SubField = RF_Field.getSubset(region=dummy1_nSet, position=NODAL)
                RF_dummy2_SubField = RF_Field.getSubset(region=dummy2_nSet, position=NODAL)
                #
                if isinstance(RF_dummy1_SubField.values[0].data, float):
                    # Then variable is a scalar:
                    RF_dummy1[iFrame] = RF_dummy1_SubField.values[0].data
                    RF_dummy2[iFrame] = RF_dummy2_SubField.values[0].data
                    #
                else:
                    # Variable is an array:
                    for j in range(0, len(RF_dummy1_SubField.values[0].data)):
                        RF_dummy1[iFrame][j] = RF_dummy1_SubField.values[0].data[j]
                        RF_dummy2[iFrame][j] = RF_dummy2_SubField.values[0].data[j]
                # Finished saving this variable at the dummy nodes!
                # Now compute the deformation gradient, jacobian and nominal stress:
                for j in range(0, 2):
                    defGrad[iFrame][0][j] = U_dummy1[iFrame][j] + eye[0][j]
                    defGrad[iFrame][1][j] = U_dummy2[iFrame][j] + eye[1][j]
                    nomP[iFrame][0][j] = RF_dummy1[iFrame][j] / tot_vol
                    nomP[iFrame][1][j] = RF_dummy2[iFrame][j] / tot_vol
                jacobian[iFrame] = numpy.linalg.det(defGrad[iFrame][:][:])
                Green_strain[iFrame, :, :] = 0.5 * (numpy.dot(numpy.transpose(defGrad[iFrame, :, :]), defGrad[iFrame, :, :]) - numpy.identity(2))
                PK2[iFrame, :, :] = numpy.dot(nomP[iFrame, :, :], numpy.linalg.inv(numpy.transpose(defGrad[iFrame, :, :])))
        # return Green_strain, PK2, tot_vol
        # Save all variables to a single structured variable with all the data
        RVE_variables = {'step_total_time': stepTotalTime,
                         'P': nomP,
                         'F': defGrad,
                         'J': jacobian,
                         'total_vol': tot_vol,
                         'Green_strain': Green_strain,
                         'PK2': PK2}
        # Save post-processing information to pkl file:
        with open('results.p', 'w') as fp:
            pickle.dump(RVE_variables, fp)