import re
import ast

import dicom_processor
import common_utils


# Standard Scan
def is_standard_scan(description):
    regexes = [
        re.compile('\\bNAC', re.IGNORECASE),
        re.compile('NAC\\b', re.IGNORECASE),
        re.compile('_NAC', re.IGNORECASE),
        re.compile('NAC_', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# Attenuation Corrected Scan
def is_attn_corr_scan(description):
    regexes = [
        re.compile('\\bAC', re.IGNORECASE),
        re.compile('AC\\b', re.IGNORECASE),
        re.compile('_AC', re.IGNORECASE),
        re.compile('^AC_', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# Scan Orientation, Axial
def is_axial(description):
    regexes = [
        re.compile('axial', re.IGNORECASE),
        re.compile('trans', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# Scan Orientation, Coronal
def is_coronal(description):
    regexes = [
        re.compile('cor', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# Scan Orientation, Sagittal
def is_sagittal(description):
    regexes = [
        re.compile('sag', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# Anatomy, Chest
def is_chest(description):
    regexes = [
        re.compile('lung', re.IGNORECASE),
        re.compile('chest', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# Anatomy, Abdomen
def is_abdomen(description):
    regexes = [
        re.compile('abd', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# Anatomy, Pelvis
def is_pelvis(description):
    regexes = [
        re.compile('pelvis', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# Anatomy, Head
def is_head(scan_coverage):
    return scan_coverage is not None and scan_coverage < 250

# Anatomy, Whole Body
def is_whole_body(scan_coverage):
    return scan_coverage is not None and scan_coverage > 1300

# Anatomy, C/A/P
def is_cap(scan_coverage):
    return scan_coverage is not None and scan_coverage > 800 and scan_coverage < 1300

# No Contrast
def is_not_contrast(description):
    regexes = [
        re.compile('w\\^o', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# Contrast
def is_contrast(description):
    regexes = [
        re.compile('w\\^IV', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# Contrast, Arterial Phase
def is_arterial_phase(description):
    regexes = [
        re.compile('arterial', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# Contrast, Portal Venous
def is_portal_venous(description):
    regexes = [
        re.compile('venous', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# Contrast, Delayed
def is_delayed(description):
    regexes = [
        re.compile('delayed', re.IGNORECASE),
        re.compile('equil', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# Reconstruction Window, Bone
def is_bone_window(description):
    regexes = [
        re.compile('bone window', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# Reconstruction Window, Lung
def is_lung_window(description):
    regexes = [
        re.compile('lung window', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)



def classify_CT(df, single_header_object, acquisition):
    '''
    Classifies a CT dicom series

    Args:
        df (DataFrame): A pandas DataFrame where each row is a dicom image header information
    Returns:
        dict: The dictionary for the CT classification
    '''
    series_description = single_header_object.get('SeriesDescription') or ''
    classifications = {}
    info_object = {}
    if common_utils.is_localizer(acquisition.label) or common_utils.is_localizer(series_description) or len(df) < 10:
        classifications['Scan Type'] = ['Localizer']
    else:
        if single_header_object['ImageType'][0] == 'DERIVED':
            classifications['Scan Type'] = ['Derived']
        
        scan_coverage = None
        if single_header_object['ImageType'][0] == 'ORIGINAL':
            scan_coverage = common_utils.compute_scan_coverage(df)
        if scan_coverage:
            info_object['ScanCoverage'] = scan_coverage
        
        # Reconstruction window
        reconstruction_window = None
        if is_bone_window(acquisition.label):
            reconstruction_window = 'Bone'
        elif is_lung_window(acquisition.label):
            reconstruction_window = 'Lung'
        if reconstruction_window:
            info_object['ReconstructionWindow'] = reconstruction_window
        
        # Scan orientation from acquisition label
        scan_orientation = None
        if is_axial(acquisition.label):
            scan_orientation = 'axial'
        elif is_coronal(acquisition.label):
            scan_orientation = 'coronal'
        elif is_sagittal(acquisition.label):
            scan_orientation = 'sagittal'
        elif is_axial(series_description):
            scan_orientation = 'axial'
        elif is_coronal(series_description):
            scan_orientation = 'coronal'
        elif is_sagittal(series_description):
            scan_orientation = 'sagittal'
        if scan_orientation:
            info_object['ScanOrientation'] = scan_orientation

        # Anatomy
        if is_chest(acquisition.label):
            classifications['Anatomy'] = ['Chest']
        elif is_abdomen(acquisition.label):
            classifications['Anatomy'] = ['Abdomen']
        elif is_pelvis(acquisition.label):
            classifications['Anatomy'] = ['Pelvis']
        elif is_chest(series_description):
            classifications['Anatomy'] = ['Chest']
        elif is_abdomen(series_description):
            classifications['Anatomy'] = ['Abdomen']
        elif is_pelvis(series_description):
            classifications['Anatomy'] = ['Pelvis']
        elif is_head(scan_coverage):
            classifications['Anatomy'] = ['Head']
        elif is_whole_body(scan_coverage):
            classifications['Anatomy'] = ['Whole Body']
        elif is_cap(scan_coverage):
            classifications['Anatomy'] = ['Chest', 'Abdomen', 'Pelvis']
        
        # Contrast
        if is_not_contrast(acquisition.label):
            classifications['Contrast'] = ['No Contrast']
        elif is_contrast(acquisition.label):
            if is_arterial_phase(acquisition.label):
                classifications['Contrast'] = ['Arterial Phase']
            elif is_delayed(acquisition.label):
                classifications['Contrast'] = ['Delayed Phase']
            elif is_portal_venous(acquisition.label):
                classifications['Contrast'] = ['Portal Venous Phase']
            else:
                classifications['Contrast'] = ['With Contrast']
        elif is_not_contrast(series_description):
            classifications['Contrast'] = ['No Contrast']
        elif is_contrast(series_description):
            if is_arterial_phase(series_description):
                classifications['Contrast'] = ['Arterial Phase']
            elif is_delayed(series_description):
                classifications['Contrast'] = ['Delayed Phase']
            elif is_portal_venous(series_description):
                classifications['Contrast'] = ['Portal Venous Phase']
            else:
                classifications['Contrast'] = ['With Contrast']

        if scan_coverage:
            spacing_between_slices = scan_coverage / len(df)
            info_object['SpacingBetweenSlices'] = round(spacing_between_slices, 2)
    return classifications, info_object
