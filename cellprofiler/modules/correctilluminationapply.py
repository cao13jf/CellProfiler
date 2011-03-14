'''<b>Correct Illumination - Apply</b> applies an illumination function, usually created by
<b>CorrectIlluminationCalculate</b>, to an image in order to correct for uneven
illumination (uneven shading)
<hr>

This module applies a previously created illumination correction function,
either loaded by <b>LoadSingleImage</b> or created by <b>CorrectIlluminationCalculate</b>.
This module corrects each image in the pipeline using the function specified. 

See also <b>CorrectIlluminationCalculate</b>.'''

# CellProfiler is distributed under the GNU General Public License.
# See the accompanying file LICENSE for details.
# 
# Developed by the Broad Institute
# Copyright 2003-2011
# 
# Please see the AUTHORS file for credits.
# 
# Website: http://www.cellprofiler.org

__version__="$Revision$"

import numpy as np

import cellprofiler.cpmodule as cpm
import cellprofiler.settings as cps
import cellprofiler.cpimage  as cpi

######################################
#
# Choices for "Divide or subtract"?
#
######################################
DOS_DIVIDE = "Divide"
DOS_SUBTRACT = "Subtract"

######################################
#
# Rescaling choices - deprecated
#
######################################
RE_NONE = "No rescaling"
RE_STRETCH = "Stretch 0 to 1"
RE_MATCH = "Match maximums"

######################################
#
# # of settings per image when writing pipeline
#
######################################

SETTINGS_PER_IMAGE = 4

class CorrectIlluminationApply(cpm.CPModule):
    category = "Image Processing"
    variable_revision_number = 3
    module_name = "CorrectIlluminationApply"

    def create_settings(self):
        """Make settings here (and set the module name)"""
        self.images = []
        self.add_image(can_delete = False)
        self.add_image_button = cps.DoSomething("", "Add another image",
                                                self.add_image)

    def add_image(self, can_delete = True):
        '''Add an image and its settings to the list of images'''
        image_name = cps.ImageNameSubscriber("Select the input image","None", doc = '''
                                        What did you call the image to be corrected?''')

        corrected_image_name = cps.ImageNameProvider("Name the output image","CorrBlue", doc = '''
                                        What do you want to call the corrected image?''')

        illum_correct_function_image_name = cps.ImageNameSubscriber("Select the illumination function","None", doc = '''
                                        What did you call the illumination correction function image that will be used to carry out the correction (produced by another module 
                                        or loaded as a .mat format image using <b>LoadSingleImage</b>)?''')

        divide_or_subtract = cps.Choice("Select how the illumination function is applied",
                                        [DOS_DIVIDE, DOS_SUBTRACT], doc = '''
                                        This choice depends on how the illumination function was calculated
                                        and on your physical model of the way illumination variation affects the background of images relative to 
                                        the objects in images; it is also somewhat empirical. 
                                        <ul>
                                        <li><i>Subtract</i>: Use this option if the background signal is significant relative to the real signal
                                        coming from the cells.  If you created the illumination correction function using <i>Background</i>,
                                        then you will want to choose <i>Subtract</i> here.</li>
                                        <li><i>Divide</i>: Choose this option if the the signal to background ratio 
                                        is high (the cells are stained very strongly). If you created the illumination correction function using <i>Regular</i>,
                                        then you will want to choose <i>Divide</i> here.</li>
                                        </ul>''')

        image_settings = cps.SettingsGroup()
        image_settings.append("image_name", image_name)
        image_settings.append("corrected_image_name", corrected_image_name)
        image_settings.append("illum_correct_function_image_name", 
                              illum_correct_function_image_name)
        image_settings.append("divide_or_subtract", divide_or_subtract)
        image_settings.append("rescale_option",RE_NONE)
        
        if can_delete:
            image_settings.append("remover",
                                  cps.RemoveSettingButton("","Remove this image",
                                                          self.images,
                                                          image_settings))
        image_settings.append("divider",cps.Divider())
        self.images.append(image_settings)

    def settings(self):
        """Return the settings to be loaded or saved to/from the pipeline

        These are the settings (from cellprofiler.settings) that are
        either read from the strings in the pipeline or written out
        to the pipeline. The settings should appear in a consistent
        order so they can be matched to the strings in the pipeline.
        """
        result = []
        for image in self.images:
            result += [image.image_name, image.corrected_image_name,
                       image.illum_correct_function_image_name, 
                       image.divide_or_subtract]
        return result

    def visible_settings(self):
        """Return the list of displayed settings
        """
        result = []
        for image in self.images:
            result += [image.image_name, image.corrected_image_name,
                       image.illum_correct_function_image_name, 
                       image.divide_or_subtract]
            #
            # Get the "remover" button if there is one
            #
            remover = getattr(image, "remover", None)
            if remover is not None:
                result.append(remover)
            result.append(image.divider)
        result.append(self.add_image_button)
        return result

    def prepare_settings(self, setting_values):
        """Do any sort of adjustment to the settings required for the given values

        setting_values - the values for the settings

        This method allows a module to specialize itself according to
        the number of settings and their value. For instance, a module that
        takes a variable number of images or objects can increase or decrease
        the number of relevant settings so they map correctly to the values.
        """
        #
        # Figure out how many images there are based on the number of setting_values
        #
        assert len(setting_values) % SETTINGS_PER_IMAGE == 0
        image_count = len(setting_values) / SETTINGS_PER_IMAGE
        del self.images[image_count:]
        while len(self.images) < image_count:
            self.add_image()

    def run(self, workspace):
        """Run the module

        workspace    - The workspace contains
            pipeline     - instance of cpp for this run
            image_set    - the images in the image set being processed
            object_set   - the objects (labeled masks) in this image set
            measurements - the measurements for this run
            frame        - the parent frame to whatever frame is created. None means don't draw.
        """
        for image in self.images:
            self.run_image(image, workspace)

    def run_image(self, image, workspace):
        '''Perform illumination according to the parameters of one image setting group

        '''
        #
        # Get the image names from the settings
        #
        image_name = image.image_name.value
        illum_correct_name = image.illum_correct_function_image_name.value
        corrected_image_name = image.corrected_image_name.value
        #
        # Get grayscale images from the image set
        #
        orig_image = workspace.image_set.get_image(image_name,
                                                   must_be_grayscale=True)
        illum_function = workspace.image_set.get_image(illum_correct_name,
                                                       must_be_grayscale=True)
        #
        # Either divide or subtract the illumination image from the original
        #
        if image.divide_or_subtract == DOS_DIVIDE:
            output_pixels = orig_image.pixel_data / illum_function.pixel_data
        elif image.divide_or_subtract == DOS_SUBTRACT:
            output_pixels = orig_image.pixel_data - illum_function.pixel_data
            output_pixels[output_pixels < 0] = 0
        else:
            raise ValueError("Unhandled option for divide or subtract: %s"%
                             image.divide_or_subtract.value)
        #
        # Save the output image in the image set and have it inherit
        # mask & cropping from the original image.
        #
        output_image = cpi.Image(output_pixels, parent_image = orig_image) 
        workspace.image_set.add(corrected_image_name, output_image)

    def display(self, workspace):
        ''' Display one row of orig / illum / output per image setting group'''
        figure = workspace.create_or_find_figure(title="CorrectIlluminationApply, image cycle #%d"%(
                workspace.measurements.image_set_number),subplots=(3,len(self.images)))
        for j, image in enumerate(self.images):
            image_name = image.image_name.value
            illum_correct_function_image_name = image.illum_correct_function_image_name.value
            corrected_image_name = image.corrected_image_name.value
            orig_image = workspace.image_set.get_image(image_name,
                                                       must_be_grayscale=True)
            illum_image = workspace.image_set.get_image(illum_correct_function_image_name,
                                                        must_be_grayscale=True)
            corrected_image = workspace.image_set.get_image(corrected_image_name)

            figure.subplot_imshow_grayscale(0, j, orig_image.pixel_data,
                                            "Original image: %s" % image_name,
                                            sharex=figure.subplot(0,0),
                                            sharey=figure.subplot(0,0))
            title = ("Illumination function: %s\nmin=%f, max=%f" %
                     (illum_correct_function_image_name,
                      round(illum_image.pixel_data.min(),4),
                      round(illum_image.pixel_data.max(),4)))

            figure.subplot_imshow_grayscale(1, j, illum_image.pixel_data, title,
                                            sharex=figure.subplot(0,0),
                                            sharey=figure.subplot(0,0))
            figure.subplot_imshow_grayscale(2, j, corrected_image.pixel_data,
                                            "Final image: %s" %
                                            corrected_image_name,
                                            sharex=figure.subplot(0,0),
                                            sharey=figure.subplot(0,0))

    def is_interactive(self):
        return False

    def validate_module_warnings(self, pipeline):
        """If a CP 1.0 pipeline used a rescaling option other than 'No rescaling', warn the user."""
        for j, image in enumerate(self.images):
            if image.rescale_option != RE_NONE:
                raise cps.ValidationError(("Your original pipeline used '%s' to rescale the final image, "
                                          "but the rescaling option has been removed. Please use "
                                          "RescaleIntensity to rescale your output image. Save your "
                                          "pipeline to get rid of this warning.")%(image.rescale_option),
                                          image.divide_or_subtract)

    def upgrade_settings(self, setting_values, variable_revision_number, 
                         module_name, from_matlab):
        """Adjust settings based on revision # of save file

        setting_values - sequence of string values as they appear in the
                         saved pipeline
        variable_revision_number - the variable revision number of the module
                                   at the time of saving
        module_name - the name of the module that did the saving
        from_matlab - True if saved in CP Matlab, False if saved in pyCP

        returns the updated setting_values, revision # and matlab flag
        """
        # No SVN records of revisions 1 & 2
        if from_matlab and variable_revision_number == 3:
            # Same order as pyCP
            from_matlab = False
            variable_revision_number = 1
        if not from_matlab and variable_revision_number == 1:
            # Added multiple settings, but, if you only had 1,
            # the order didn't change
            variable_revision_number = 2

        if not from_matlab and variable_revision_number == 2:
            # If revsion < 2, remove rescaling option; warning user and suggest RescaleIntensity instead.
            # Keep the prior selection around for the validation warning.
            SLOT_RESCALE_OPTION = 4
            SETTINGS_PER_IMAGE_V2 = 5
            rescale_option = setting_values[SLOT_RESCALE_OPTION::SETTINGS_PER_IMAGE_V2]
            for i,image in enumerate(self.images):
                image.rescale_option = rescale_option[i] 
            del setting_values[SLOT_RESCALE_OPTION::SETTINGS_PER_IMAGE_V2]
            
            variable_revision_number = 3
        else:
            # If revision >= 2, initalize rescaling option for validation warning 
            for i,image in enumerate(self.images):
                image.rescale_option = RE_NONE
        
        return setting_values, variable_revision_number, from_matlab


