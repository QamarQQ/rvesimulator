#                                                                       Modules
# =============================================================================
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


class HollowPlate:
    def __init__(self, point1, point2, center, radius, name_part, model):
        """initialization of the hollow plate simulation

        Parameters
        ----------
        point1 : float
            first point of the square
        point2 : float
            second point of the square
        center : float
            center of the circle
        radius : float
            radius of the circle
        name_part : str
            name of the part
        model : abaqus model
            abaqus model
        """
        self.part = None
        self.assembly = None
        self.model = model
        self.part_name = name_part
        self.point1 = point1
        self.point2 = point2
        self.center = center
        self.radius = radius

    def create_part(self):
        sketch = self.model.ConstrainedSketch(
            name="sketch_profile", sheetSize=10.0
        )
        sketch.rectangle(point1=self.point1, point2=self.point2)
        sketch.CircleByCenterPerimeter(
            center=self.center, point1=(self.radius, 0.0)
        )
        self.part = self.model.Part(
            name=self.part_name,
            dimensionality=TWO_D_PLANAR,
            type=DEFORMABLE_BODY,
        )
        self.part.BaseShell(sketch=sketch)

        return self.part


# =============================================================================


class CircleInclusion:
    def __init__(
        self,
        model,
        loc_info,
        model_name,
        part_name,
        instance_name,
    ):
        """initilaization of circle inclusion rve

        Parameters
        ----------
        model : abaqus model
            abaqus model
        loc_info : list
            location of circles
        model_name : str
            model name
        part_name : str
            abaqus part name
        instance_name : str
            abaqus instance name
        """
        self.model = model
        # define the reinforcement information
        self.loc = loc_info["location_information"]
        # define the boundaries of the square
        self.a0 = loc_info["len_start"]
        self.af = loc_info["len_end"]
        self.b0 = loc_info["wid_start"]
        self.bf = loc_info["wid_end"]

        # define the radius info
        self.radius = loc_info["radius"]
        # specify the names of simulation
        self.model_name = model_name
        self.part_name = part_name
        self.instance_name = instance_name
        self.part = None
        self.assembly = None

    def create_part(self):
        """create part

        Returns
        -------
        abaqus part
            abaqus part
        """

        # Create the  fibers
        sketch = self.model.ConstrainedSketch(
            name="__profile__", sheetSize=0.050
        )
        for ii in range(len(self.loc)):
            sketch.CircleByCenterPerimeter(
                center=(self.loc[ii][0], self.loc[ii][1]),
                point1=(self.loc[ii][0] + self.radius, self.loc[ii][1]),
            )
        self.model.ConstrainedSketch(
            name="Fibre_Sketch_Prov", objectToCopy=sketch
        )
        self.model.sketches.changeKey(
            fromName="__profile__", toName="Fibre_Sketch_Prov"
        )

        # create a frame to cut the fibers so they can stay inside the square
        sketch = self.model.ConstrainedSketch(
            name="__profile__", sheetSize=self.af
        )
        sketch.rectangle(
            point1=(self.a0 + self.radius, self.b0 + self.radius),
            point2=(self.af - self.radius, self.bf - self.radius),
        )
        sketch.rectangle(
            point1=(self.a0 - self.radius, self.b0 - self.radius),
            point2=(self.af + self.radius, self.bf + self.radius),
        )
        self.model.sketches.changeKey(
            fromName="__profile__", toName="Fibre_Sketch_Trim"
        )

        #  Matrix Sketch
        sketch = self.model.ConstrainedSketch(
            name="__profile__", sheetSize=self.af
        )
        sketch.rectangle(
            point1=(self.a0 + self.radius, self.b0 + self.radius),
            point2=(self.af - self.radius, self.bf - self.radius),
        )
        self.model.sketches.changeKey(
            fromName="__profile__", toName="Matrix_Sketch"
        )

        # Fibres Part (Provisional): before trim
        sketch = self.model.ConstrainedSketch(
            name="__profile__", sheetSize=self.af
        )
        sketch.retrieveSketch(sketch=self.model.sketches["Fibre_Sketch_Prov"])
        self.part = self.model.Part(
            name="Fibre_Part_Prov",
            dimensionality=TWO_D_PLANAR,
            type=DEFORMABLE_BODY,
        )
        self.part = self.model.parts["Fibre_Part_Prov"]
        self.part.BaseShell(sketch=sketch)
        self.part = self.model.parts["Fibre_Part_Prov"]
        del self.model.sketches["__profile__"]
        del self.model.sketches["Fibre_Sketch_Prov"]

        # trim part
        sketch = self.model.ConstrainedSketch(
            name="__profile__", sheetSize=self.af
        )
        sketch.retrieveSketch(sketch=self.model.sketches["Fibre_Sketch_Trim"])
        self.part = self.model.Part(
            name="Fibre_Part_Trim",
            dimensionality=TWO_D_PLANAR,
            type=DEFORMABLE_BODY,
        )
        self.part = self.model.parts["Fibre_Part_Trim"]
        self.part.BaseShell(sketch=sketch)
        self.part = self.model.parts["Fibre_Part_Trim"]
        del self.model.sketches["__profile__"]
        del self.model.sketches["Fibre_Sketch_Trim"]

        # The original square part (matrix part)
        sketch = self.model.ConstrainedSketch(
            name="__profile__", sheetSize=self.af
        )
        sketch.retrieveSketch(sketch=self.model.sketches["Matrix_Sketch"])
        self.part = self.model.Part(
            name="Matrix_Part",
            dimensionality=TWO_D_PLANAR,
            type=DEFORMABLE_BODY,
        )
        self.part = self.model.parts["Matrix_Part"]
        self.part.BaseShell(sketch=sketch)
        self.part = self.model.parts["Matrix_Part"]
        del self.model.sketches["__profile__"]
        del self.model.sketches["Matrix_Sketch"]

        # Fibre Part
        self.assembly = self.model.rootAssembly
        self.part = self.model.parts["Fibre_Part_Prov"]
        self.assembly.Instance(
            name="Fibre_Instance_Prov", part=self.part, dependent=ON
        )
        self.part = self.model.parts["Fibre_Part_Trim"]
        self.assembly.Instance(
            name="Fibre_Instance_Trim", part=self.part, dependent=ON
        )
        self.assembly.InstanceFromBooleanCut(
            name="Fibre_Final_Part",
            instanceToBeCut=self.assembly.instances["Fibre_Instance_Prov"],
            cuttingInstances=(self.assembly.instances["Fibre_Instance_Trim"],),
            originalInstances=DELETE,
        )
        self.assembly.makeIndependent(
            instances=(self.assembly.instances["Fibre_Final_Part-1"],)
        )
        self.model.rootAssembly.features.changeKey(
            fromName="Fibre_Final_Part-1", toName="Fibre_Final_Instance"
        )
        del self.model.parts["Fibre_Part_Prov"]
        del self.model.parts["Fibre_Part_Trim"]

        # Matrix Part
        self.assembly = self.model.rootAssembly
        self.part = self.model.parts["Matrix_Part"]
        self.assembly.Instance(
            name="Matrix_Instance", part=self.part, dependent=ON
        )
        self.assembly.InstanceFromBooleanCut(
            name="Matrix_Final_Part",
            instanceToBeCut=self.assembly.instances["Matrix_Instance"],
            cuttingInstances=(
                self.assembly.instances["Fibre_Final_Instance"],
            ),
            originalInstances=DELETE,
        )
        self.assembly.makeIndependent(
            instances=(self.assembly.instances["Matrix_Final_Part-1"],)
        )
        self.assembly.features.changeKey(
            fromName="Matrix_Final_Part-1", toName="Matrix_Final_Instance"
        )
        del self.model.parts["Matrix_Part"]

        # Assembly and Meshing
        self.part = self.model.parts["Fibre_Final_Part"]
        self.assembly.Instance(
            name="Fibre_Final_Instance", part=self.part, dependent=ON
        )
        self.assembly.InstanceFromBooleanMerge(
            name="Final_Stuff",
            instances=(
                self.assembly.instances["Matrix_Final_Instance"],
                self.assembly.instances["Fibre_Final_Instance"],
            ),
            keepIntersections=ON,
            originalInstances=DELETE,
            domain=GEOMETRY,
        )
        del self.model.parts["Matrix_Final_Part"]
        del self.model.parts["Fibre_Final_Part"]

        return self.part


# =============================================================================
class FullCircleInclusion:
    def __init__(
        self,
        model,
        loc_info,
        model_name,
        part_name,
        instance_name,
    ):
        """initilaization of circle inclusion rve

        Parameters
        ----------
        model : abaqus model
            abaqus model
        loc_info : list
            location of circles
        model_name : str
            model name
        part_name : str
            abaqus part name
        instance_name : str
            abaqus instance name
        """
        self.model = model
        # define the reinforcement information
        self.loc = loc_info["location_information"]
        # define the boundaries of the square
        self.a0 = loc_info["len_start"]
        self.af = loc_info["len_end"]
        self.b0 = loc_info["wid_start"]
        self.bf = loc_info["wid_end"]
        # define the radius info
        self.radius = loc_info["radius"]
        # specify the names of simulation
        self.model_name = model_name
        self.part_name = part_name
        self.instance_name = instance_name
        self.part = None
        self.assembly = None

    def create_part(self):

        # Create the  fibers
        sketch = self.model.ConstrainedSketch(
            name="__profile__", sheetSize=self.af
        )
        for ii in range(len(self.loc)):
            sketch.CircleByCenterPerimeter(
                center=(self.loc[ii][0], self.loc[ii][1]),
                point1=(self.loc[ii][0] + self.radius, self.loc[ii][1]),
            )
        self.model.ConstrainedSketch(
            name="Fibre_Sketch_Prov", objectToCopy=sketch
        )
        self.model.sketches.changeKey(
            fromName="__profile__", toName="Fibre_Sketch_Prov"
        )
        # Matrix Sketch
        sketch = self.model.ConstrainedSketch(
            name="__profile__", sheetSize=self.af
        )
        sketch.rectangle(
            point1=(self.a0 + self.radius, self.b0 + self.radius),
            point2=(self.af - self.radius, self.bf - self.radius),
        )
        self.model.sketches.changeKey(
            fromName="__profile__", toName="Matrix_Sketch"
        )

        # Fibres Part
        sketch = self.model.ConstrainedSketch(
            name="__profile__", sheetSize=self.af
        )
        sketch.retrieveSketch(sketch=self.model.sketches["Fibre_Sketch_Prov"])
        self.part = self.model.Part(
            name="Fibre_Final_Part",
            dimensionality=TWO_D_PLANAR,
            type=DEFORMABLE_BODY,
        )
        self.part = self.model.parts["Fibre_Final_Part"]
        self.part.BaseShell(sketch=sketch)
        self.part = self.model.parts["Fibre_Final_Part"]

        del self.model.sketches["__profile__"]
        del self.model.sketches["Fibre_Sketch_Prov"]

        # The original square part (matrix part)
        sketch = self.model.ConstrainedSketch(
            name="__profile__", sheetSize=self.af
        )
        sketch.retrieveSketch(sketch=self.model.sketches["Matrix_Sketch"])
        self.part = self.model.Part(
            name="Matrix_Part",
            dimensionality=TWO_D_PLANAR,
            type=DEFORMABLE_BODY,
        )
        self.part = self.model.parts["Matrix_Part"]
        self.part.BaseShell(sketch=sketch)
        self.part = self.model.parts["Matrix_Part"]
        del self.model.sketches["__profile__"]
        del self.model.sketches["Matrix_Sketch"]

        # Fibre Part
        self.assembly = self.model.rootAssembly
        self.part = self.model.parts["Fibre_Final_Part"]
        self.assembly.Instance(
            name="Fibre_Final_Instance", part=self.part, dependent=ON
        )
        # Matrix Part
        self.assembly = self.model.rootAssembly
        self.part = self.model.parts["Matrix_Part"]
        self.assembly.Instance(
            name="Matrix_Instance", part=self.part, dependent=ON
        )
        self.assembly.InstanceFromBooleanCut(
            name="Matrix_Final_Part",
            instanceToBeCut=self.assembly.instances["Matrix_Instance"],
            cuttingInstances=(
                self.assembly.instances["Fibre_Final_Instance"],
            ),
            originalInstances=DELETE,
        )
        self.assembly.makeIndependent(
            instances=(self.assembly.instances["Matrix_Final_Part-1"],)
        )
        self.assembly.features.changeKey(
            fromName="Matrix_Final_Part-1", toName="Matrix_Final_Instance"
        )
        del self.model.parts["Matrix_Part"]

        # Assembly
        self.part = self.model.parts["Fibre_Final_Part"]
        self.assembly.Instance(
            name="Fibre_Final_Instance", part=self.part, dependent=ON
        )
        self.assembly.InstanceFromBooleanMerge(
            name="Final_Stuff",
            instances=(
                self.assembly.instances["Matrix_Final_Instance"],
                self.assembly.instances["Fibre_Final_Instance"],
            ),
            keepIntersections=ON,
            originalInstances=DELETE,
            domain=GEOMETRY,
        )
        del self.model.parts["Matrix_Final_Part"]
        del self.model.parts["Fibre_Final_Part"]

        return self.part
