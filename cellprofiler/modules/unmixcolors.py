'''<b>Unmix Colors</b> creates separate images per dye stain for histologically
stained images
<hr>

This module creates separate grayscale images from a color image stained
with light-absorbing dyes. Dyes are assumed to absorb an amount of light
in the red, green and blue channels that increases proportionally in each
channel with increasing amounts of stain; the hue does not shift with
increasing staining.

The module separates two or more stains from a background, producing grayscale
images. There are several pre-set dye combinations as well as a custom
mode that allows a user to calibrate using two images stained with a single
dye each.

Some commonly known stains must be specified by the individual dye components. For
example:
<ul>
<li>Azan-Mallory: Anilline Blue + Azocarmine + Orange-G</li>
<li>Giemsa: Methylene Blue or Eosin</li>
<li>Masson Trichrome: Methyl blue + Ponceau-Fuchsin</li>
</ul>
If there are non-stained cells/components that you also want to separate by color,
choose the stain that closest resembles the color you want, or enter a custom value.

<h3>Technical notes</h3>
This code is adapted from the ImageJ plugin, <i>Colour_Deconvolution.java</i>
(described <a href="http://www.dentistry.bham.ac.uk/landinig/software/cdeconv/cdeconv.html">here</a>)
written by A.C. Ruifrok, whose paper forms the basis for this code.

References
<ul>
<li>Ruifrok AC, Johnston DA. <i>Quantification of histochemical staining by color 
deconvolution.</i> Analytical & Quantitative Cytology & Histology 2001; 23: 291-299.</li>
</ul>
'''
# CellProfiler is distributed under the GNU General Public License.
# See the accompanying file LICENSE for details.
# 
# Developed by the Broad Institute
# Copyright 2003-2011
# 
# Please see the AUTHORS file for credits.
# 
# Website: http://www.cellprofiler.org

__version__ = "$Revision$"

import numpy as np
from scipy.linalg import lstsq

import cellprofiler.cpmodule as cpm
import cellprofiler.settings as cps
import cellprofiler.cpimage as cpi
import cellprofiler.preferences as cpprefs

def html_color(rgb):
    '''Return an HTML color for a given stain'''
    rgb = np.exp(-np.array(rgb)) * 255
    rgb = rgb.astype(int)
    color = hex((rgb[0] * 256 + rgb[1])*256 + rgb[2])
    if color.endswith("L"):
        color = color[:-1]
    return "#"+color[2:]
    
CHOICE_HEMATOXYLIN = "Hematoxylin"
ST_HEMATOXYLIN = (0.644, 0.717, 0.267)
COLOR_HEMATOXYLIN = html_color(ST_HEMATOXYLIN)

CHOICE_EOSIN = "Eosin"
ST_EOSIN = (0.093, 0.954, 0.283)
COLOR_EOSIN = html_color(ST_EOSIN)

CHOICE_DAB = "DAB"
ST_DAB = (0.268, 0.570, 0.776)
COLOR_DAB = html_color(ST_DAB)

CHOICE_FAST_RED = "Fast red"
ST_FAST_RED = (0.214, 0.851, 0.478)
COLOR_FAST_RED = html_color(ST_FAST_RED)

CHOICE_FAST_BLUE = "Fast blue"
ST_FAST_BLUE = (0.749, 0.606, 0.267)
COLOR_FAST_BLUE = html_color(ST_FAST_BLUE)

CHOICE_METHYL_BLUE = "Methyl blue"
ST_METHYL_BLUE = (0.799, 0.591, 0.105)
COLOR_METHYL_BLUE = html_color(ST_METHYL_BLUE)

CHOICE_METHYL_GREEN = "Methyl green"
ST_METHYL_GREEN = (0.980, 0.144, 0.133)
COLOR_METHYL_GREEN = html_color(ST_METHYL_GREEN)

CHOICE_AEC = "AEC"
ST_AEC = ( 0.274, 0.679, 0.680)
COLOR_AEC = html_color(ST_AEC)

CHOICE_ANILINE_BLUE = "Aniline blue"
ST_ANILINE_BLUE = ( 0.853, 0.509, 0.113)
COLOR_ANILINE_BLUE = html_color(ST_ANILINE_BLUE)

CHOICE_AZOCARMINE = "Azocarmine"
ST_AZOCARMINE = ( 0.071, 0.977, 0.198)
COLOR_AZOCARMINE = html_color(ST_AZOCARMINE)

CHOICE_ALICAN_BLUE = "Alican blue"
ST_ALICAN_BLUE = ( 0.875, 0.458, 0.158)
COLOR_ALICAN_BLUE = html_color(ST_ALICAN_BLUE)

CHOICE_PAS = "PAS"
ST_PAS = ( 0.175, 0.972, 0.155)
COLOR_PAS = html_color(ST_PAS)

CHOICE_HEMATOXYLIN_AND_PAS = "Hematoxylin and PAS"
ST_HEMATOXYLIN_AND_PAS = ( 0.553, 0.754, 0.354)
COLOR_HEMATOXYLIN_AND_PAS = html_color(ST_HEMATOXYLIN_AND_PAS)

CHOICE_FEULGEN = "Feulgen"
ST_FEULGEN = ( 0.464, 0.830, 0.308)
COLOR_FEULGEN = html_color(ST_FEULGEN)

CHOICE_METHYLENE_BLUE = "Methylene blue"
ST_METHYLENE_BLUE  = ( 0.553, 0.754, 0.354)
COLOR_METHYLENE_BLUE  = html_color(ST_METHYLENE_BLUE)

CHOICE_ORANGE_G = "Orange-G"
ST_ORANGE_G  = ( 0.107, 0.368, 0.923)
COLOR_ORANGE_G  = html_color(ST_ORANGE_G)

CHOICE_PONCEAU_FUCHSIN = "Ponceau-fuchsin"
ST_PONCEAU_FUCHSIN  = ( 0.107, 0.368, 0.923)
COLOR_PONCEAU_FUCHSIN  = html_color(ST_PONCEAU_FUCHSIN)

CHOICE_CUSTOM = "Custom"

STAIN_DICTIONARY = {
    CHOICE_AEC: ST_AEC,
    CHOICE_ALICAN_BLUE: ST_ALICAN_BLUE,
    CHOICE_ANILINE_BLUE: ST_ANILINE_BLUE,
    CHOICE_AZOCARMINE: ST_AZOCARMINE,
    CHOICE_DAB: ST_DAB,
    CHOICE_EOSIN: ST_EOSIN,
    CHOICE_FAST_BLUE: ST_FAST_BLUE,
    CHOICE_FAST_RED: ST_FAST_RED,
    CHOICE_FEULGEN: ST_FEULGEN,
    CHOICE_HEMATOXYLIN: ST_HEMATOXYLIN,
    CHOICE_HEMATOXYLIN_AND_PAS: ST_HEMATOXYLIN_AND_PAS,
    CHOICE_METHYL_BLUE: ST_METHYL_BLUE,
    CHOICE_METHYLENE_BLUE: ST_METHYLENE_BLUE,
    CHOICE_METHYL_GREEN: ST_METHYL_GREEN,
    CHOICE_ORANGE_G : ST_ORANGE_G,
    CHOICE_PAS: ST_PAS,
    CHOICE_PONCEAU_FUCHSIN: ST_PONCEAU_FUCHSIN}

STAINS_BY_POPULARITY = ( 
    CHOICE_HEMATOXYLIN, CHOICE_EOSIN, CHOICE_DAB,
    CHOICE_PAS, CHOICE_AEC, CHOICE_ALICAN_BLUE, CHOICE_ANILINE_BLUE,
    CHOICE_AZOCARMINE, CHOICE_FAST_BLUE, CHOICE_FAST_RED,
    CHOICE_HEMATOXYLIN_AND_PAS, CHOICE_METHYL_GREEN, CHOICE_METHYLENE_BLUE,
    CHOICE_ORANGE_G, CHOICE_METHYL_BLUE, CHOICE_PONCEAU_FUCHSIN, 
    CHOICE_METHYL_BLUE, CHOICE_FEULGEN)

FIXED_SETTING_COUNT = 2
VARIABLE_SETTING_COUNT = 5

class UnmixColors(cpm.CPModule):
    module_name = "UnmixColors"
    category = "Image Processing"
    variable_revision_number = 2
    
    def create_settings(self):
        self.outputs = []
        self.stain_count = cps.HiddenCount(self.outputs, "Stain count")
        self.input_image_name = cps.ImageNameSubscriber(
            "Color image", "None",
            doc = """Choose the name of the histologically stained color image
            loaded or created by some prior module.""")
        self.add_image(False)
        self.add_image_button = cps.DoSomething(
            "Add another stain", "Add stain", self.add_image,
            doc = """Press this button to add another stain to the list.
            You will be able to name the image produced and to either pick
            the stain from a list of precalibrated stains or to enter
            custom values for the stain's red, green and blue absorbance.""")
        
    def add_image(self, can_remove = True):
        group = cps.SettingsGroup()
        group.can_remove = can_remove
        if can_remove:
            group.append("divider", cps.Divider())
        idx = len(self.outputs)
        default_name = STAINS_BY_POPULARITY[idx % len(STAINS_BY_POPULARITY)]
        default_name = default_name.replace(" ","")
        group.append("image_name", cps.ImageNameProvider(
            "Image name", default_name,
            doc = """Use this setting to name one of the images produced by the
            module for a particular stain. The image can be used in
            subsequent modules in the pipeline."""))
        choices = list(sorted(STAIN_DICTIONARY.keys())) + [ CHOICE_CUSTOM ]
        group.append("stain_choice", cps.Choice(
            "Stain", choices = choices,
            doc = """Use this setting to choose the absorbance values for a
            particular stain. The stains are:
            <br>
            <table><tr><th>Stain</th><th>Color</th><th>Specific to</th></tr>
            <tr><td>%(CHOICE_AEC)s (3-Amino-9-ethylcarbazole)</td><td bgcolor="%(COLOR_AEC)s">&nbsp;</td><td>Peroxidase</td></tr>
            <tr><td>%(CHOICE_ALICAN_BLUE)s</td><td bgcolor="%(COLOR_ALICAN_BLUE)s">&nbsp;</td><td>Mucopolysaccharides</td></tr>
            <tr><td>%(CHOICE_ANILINE_BLUE)s</td><td bgcolor="%(COLOR_ANILINE_BLUE)s">&nbsp;</td><td>Pollen tubes</td></tr>
            <tr><td>%(CHOICE_AZOCARMINE)s</td><td bgcolor="%(COLOR_AZOCARMINE)s">&nbsp;</td><td>Plasma</td></tr>
            <tr><td>%(CHOICE_DAB)s</td><td bgcolor="%(COLOR_DAB)s">&nbsp;</td><td>Peroxisomes, mitochondria</td></tr>
            <tr><td>%(CHOICE_EOSIN)s</td><td bgcolor="%(COLOR_EOSIN)s">&nbsp;</td><td>Elastic, collagen and reticular fibers</td></tr>
            <tr><td>%(CHOICE_FAST_RED)s</td><td bgcolor="%(COLOR_FAST_RED)s">&nbsp;</td><td>Nuclei</td></tr>
            <tr><td>%(CHOICE_FAST_BLUE)s</td><td bgcolor="%(COLOR_FAST_BLUE)s">&nbsp;</td><td>Myelin fibers</td></tr>
            <tr><td>%(CHOICE_FEULGEN)s</td><td bgcolor="%(COLOR_FEULGEN)s">&nbsp;</td><td>DNA</td></tr>
            <tr><td>%(CHOICE_HEMATOXYLIN)s</td><td bgcolor="%(COLOR_HEMATOXYLIN)s">&nbsp;</td><td>Nucleic acids, endoplasmic reticulum</td></tr>
            <tr><td>%(CHOICE_HEMATOXYLIN_AND_PAS)s</td><td bgcolor="%(COLOR_HEMATOXYLIN_AND_PAS)s">&nbsp;</td><td>Nucleus (stained with both Hematoxylin and PAS)</td></tr>
            <tr><td>%(CHOICE_METHYL_BLUE)s</td><td bgcolor="%(COLOR_METHYL_BLUE)s">&nbsp;</td><td>Collagen</td></tr>
            <tr><td>%(CHOICE_METHYL_GREEN)s</td><td bgcolor="%(COLOR_METHYL_GREEN)s">&nbsp;</td><td>Chromatin</td></tr>
            <tr><td>%(CHOICE_METHYLENE_BLUE)s</td><td bgcolor="%(COLOR_METHYLENE_BLUE)s">&nbsp;</td><td>Nuclei</td></tr>
            <tr><td>%(CHOICE_ORANGE_G)s</td><td bgcolor="%(COLOR_ORANGE_G)s">&nbsp;</td><td>Erythrocytes, pancreas, pituitary</td></tr>
            <tr><td>%(CHOICE_PAS)s</td><td bgcolor="%(COLOR_PAS)s">&nbsp;</td><td>Glycogen, carbohydrates</td></tr>
            <tr><td>%(CHOICE_PONCEAU_FUCHSIN)s</td><td bgcolor="%(COLOR_PONCEAU_FUCHSIN)s">&nbsp;</td><td>Red counterstain for Masson's trichrome</td></tr>
            </table>
            <br>
            (Information taken from <a href="http://en.wikipedia.org/wiki/Histology#Staining">here</a>,
            <a href="http://en.wikipedia.org/wiki/Staining">here</a>, and
            <a href="http://stainsfile.info">here</a>.)
            <br>
            You can choose <i>%(CHOICE_CUSTOM)s</i> and enter your custom 
            values for the absorbance (or use the estimator to determine values 
            from a single-stain image).
            """ % globals()))
        group.append("red_absorbance", cps.Float(
            "Red absorbance", .5, 0, 1,
            doc = """<i>(Used only if Custom is selected for the stain)</i><br>
            The red absorbance setting estimates the dye's
            absorbance of light in the red channel.You should enter a value
            between 0 and 1 where 0 is no absorbance and 1 is complete
            absorbance. You can use the estimator to calculate this
            value automatically."""))
        group.append("green_absorbance", cps.Float(
            "Green absorbance", .5, 0, 1,
            doc = """<i>(Used only if Custom is selected for the stain)</i><br>
            The green absorbance setting estimates the dye's
            absorbance of light in the green channel. You should enter a value
            between 0 and 1 where 0 is no absorbance and 1 is complete
            absorbance. You can use the estimator to calculate this
            value automatically."""))
        group.append("blue_absorbance", cps.Float(
            "Blue absorbance", .5, 0, 1,
            doc = """<i>(Used only if Custom is selected for the stain)</i><br>
            The blue absorbance setting estimates the dye's
            absorbance of light in the blue channel. You should enter a value
            between 0 and 1 where 0 is no absorbance and 1 is complete
            absorbance. You can use the estimator to calculate this
            value automatically."""))
        
        def on_estimate():
            result = self.estimate_absorbance()
            if result is not None:
                (group.red_absorbance.value,
                 group.green_absorbance.value,
                 group.blue_absorbance.value) = result
        group.append("estimator_button", cps.DoSomething(
            "Estimate absorbance from image", "Estimate", on_estimate,
            doc = """Press this button to load an image of a sample stained
            only with the dye of interest. <b>UnmixColors</b> will estimate
            appropriate red, green and blue absorbance values from the
            image."""))
        if can_remove:
            group.append("remover", cps.RemoveSettingButton(
                "", "Remove image", self.outputs, group))
        self.outputs.append(group)
    
    def settings(self):
        '''The settings as saved to or loaded from the pipeline'''
        result = [ self.stain_count, self.input_image_name]
        for output in self.outputs:
            result += [output.image_name, output.stain_choice,
                       output.red_absorbance, output.green_absorbance,
                       output.blue_absorbance]
        return result
    
    def visible_settings(self):
        '''The settings visible to the user'''
        result = [ self.input_image_name ]
        for output in self.outputs:
            if output.can_remove:
                result += [output.divider]
            result += [output.image_name, output.stain_choice]
            if output.stain_choice == CHOICE_CUSTOM:
                result += [ output.red_absorbance, output.green_absorbance,
                            output.blue_absorbance, output.estimator_button]
            if output.can_remove:
                result += [output.remover]
        result += [self.add_image_button]
        return result
    
    def is_interactive(self):
        return False
    
    def run(self, workspace):
        '''Unmix the colors on an image in the image set'''
        input_image_name = self.input_image_name.value
        input_image = workspace.image_set.get_image(input_image_name,
                                                    must_be_rgb = True)
        input_pixels = input_image.pixel_data
        for output in self.outputs:
            self.run_on_output(workspace, input_image, output)
            
    def run_on_output(self, workspace, input_image, output):
        '''Produce one image - storing it in the image set'''
        input_pixels = input_image.pixel_data
        inverse_absorbances = self.get_inverse_absorbances(output)
        #########################################
        #
        # Renormalize to control for the other stains
        #
        # Log transform the image data
        #
        # First, rescale it a little to offset it from zero
        #
        eps = 1.0 / 256.0 / 2.0
        image = input_pixels + eps
        log_image = np.log(image)
        #
        # Now multiply the log-transformed image
        #
        scaled_image = log_image * inverse_absorbances[np.newaxis, np.newaxis, :]
        #
        # Exponentiate to get the image without the dye effect
        #
        image = np.exp(np.sum(scaled_image, 2))
        #
        # and subtract out the epsilon we originally introduced
        #
        image -= eps
        image[image < 0] = 0
        image[image > 1] = 1
        image = 1 - image
        image_name = output.image_name.value
        output_image = cpi.Image(image, parent_image = input_image)
        workspace.image_set.add(image_name, output_image)
        
    def display(self, workspace):
        '''Display all of the images in a figure'''
        figure = workspace.create_or_find_figure(title="UnmixColors, image cycle #%d"%(
                workspace.measurements.image_set_number),subplots=(len(self.outputs)+1,1))
        image_set = workspace.image_set
        assert isinstance(image_set, cpi.ImageSet)
        input_image_name = self.input_image_name.value
        input_image = image_set.get_image(input_image_name,
                                          must_be_color = True)
        figure.subplot_imshow_color(0,0, input_image.pixel_data,
                                    title = input_image_name)
        ax = figure.subplot(0,0)
        for i, output in enumerate(self.outputs):
            image_name = output.image_name.value
            output_image = image_set.get_image(image_name,
                                               must_be_grayscale = True)
            figure.subplot_imshow_grayscale(i+1, 0, output_image.pixel_data,
                                            title = image_name,
                                            sharex = ax, sharey = ax)

    def get_absorbances(self, output):
        '''Given one of the outputs, return the red, green and blue absorbance'''
        
        if output.stain_choice == CHOICE_CUSTOM:
            result = np.array(
                (output.red_absorbance.value,
                 output.green_absorbance.value,
                 output.blue_absorbance.value))
        else:
            result = STAIN_DICTIONARY[output.stain_choice.value]
        result = np.array(result)
        result = result / np.sqrt(np.sum(result**2))
        return result
    
    def get_inverse_absorbances(self, output):
        '''Get the inverse of the absorbance matrix corresponding to the output
        
        output - one of the rows of self.output
        
        returns a 3-tuple which is the column of the inverse of the matrix
        of absorbances corresponding to the entered row.
        '''
        idx = self.outputs.index(output)
        absorbance_array = np.array([self.get_absorbances(o)
                                     for o in self.outputs])
        absorbance_matrix = np.matrix(absorbance_array)
        return np.array(absorbance_matrix.I[:,idx]).flatten()
    
    def estimate_absorbance(self):
        '''Load an image and use it to estimate the absorbance of a stain
        
        Returns a 3-tuple of the R/G/B absorbances
        '''
        
        from cellprofiler.modules.loadimages import LoadImagesImageProvider
        import wx

        dlg = wx.FileDialog(
            None, "Choose reference image",
            cpprefs.get_default_image_directory())
        dlg.Wildcard = ("Image file (*.tif, *.tiff, *.bmp, *.png, *.gif, *.jpg)|"
                        "*.tif;*.tiff;*.bmp;*.png;*.gif;*.jpg")
        if dlg.ShowModal() == wx.ID_OK:
            lip = LoadImagesImageProvider("dummy","", dlg.Path)
            image = lip.provide_image(None).pixel_data
            if image.ndim < 3:
                wx.MessageBox("You must calibrate the absorbance using a color image",
                              "Error: not color image",
                              style=wx.OK | wx.ICON_ERROR)
                return None
            #
            # Log-transform the image
            #
            eps = 1.0 / 256.0 / 2.0
            log_image = np.log(image + eps)
            data = [- log_image[:,:,i].flatten() for i in range(3)]
            #
            # Order channels by strength
            #
            sums = [np.sum(x) for x in data]
            order = np.lexsort([sums])
            #
            # Calculate relative absorbance against the strongest.
            # Fit Ax = y to find A where x is the strongest and y
            # is each in turn.
            #
            strongest = data[order[-1]][:, np.newaxis]
            absorbances = [ lstsq(strongest, d)[0][0] for d in data ]
            #
            # Normalize
            #
            absorbances = np.array(absorbances)
            return absorbances / np.sqrt(np.sum(absorbances ** 2))
        return None

    def prepare_settings(self, setting_values):
        stain_count = int(setting_values[0])
        if len(self.outputs) > stain_count:
            del self.outputs[stain_count:]
        while len(self.outputs) < stain_count:
            self.add_image()
            
    def upgrade_settings(self, setting_values, variable_revision_number, module_name, from_matlab):
        if from_matlab and variable_revision_number == 0: # If coming from DifferentiateStains, no variable revision number
            setting_values = list(setting_values)
            stain1_absorbance = str.split(setting_values[5],',')
            stain2_absorbance = str.split(setting_values[6],',')
            new_setting_values = ['2', # Stain count
                                  setting_values[0],     # Input image
                                  setting_values[1],     # Output image name1
                                  CHOICE_CUSTOM,         # Output stain1 choice for stain1
                                  str(float(stain1_absorbance[0])),  # Red absorbance for stain1
                                  str(float(stain1_absorbance[1])),  # Green absorbance for stain1
                                  str(float(stain1_absorbance[2])),  # Blue absorbance for stain1
                                  setting_values[2],     # Output image name2
                                  CHOICE_CUSTOM,         # Output stain1 choice for stain2
                                  str(float(stain2_absorbance[0])),  # Red absorbance for stain2
                                  str(float(stain2_absorbance[1])),  # Green absorbance for stain2
                                  str(float(stain2_absorbance[2]))]  # Blue absorbance for stain2
            setting_values = new_setting_values
            from_matlab = False
            variable_revision_number = 2
            
        return setting_values, variable_revision_number, from_matlab
    
