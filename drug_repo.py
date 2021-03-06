# Copyright 2014 Sandra Giuliani 
# drug_repo.py

# Mapping of known drugs from ChEMBL and DrugBank to their targets/domain 
# architecture to identify suitable drug repositioning candidates for 
# schistosomiasis.
# Please see README.md for more info.




############################################################################
### import modules, set up logger
############################################################################

# import os (old system)
import os
# os system does not work very well, it is deprecated, use subprocess
#os.system('./../archSchema/bin/archindex -u B6DTB2 > test2.txt')

# import subprocess for executing command line
import subprocess

# import other modules
import sys, re, string, fnmatch, shutil

# set up log
import logging
# set up log file to write to, it will be overwritten every time ('w' mode)
# leave this level setting to DEBUG
logging.basicConfig(filename='log_drug_repo.log', filemode='w', 
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)
# leave this level setting to DEBUG
logger.setLevel(logging.DEBUG)
# create console handler
ch = logging.StreamHandler()
# CHANGE THIS TO TUNE LOGGING LEVEL from DEBUG/INFO/WARNING
ch.setLevel(logging.DEBUG)
# create formatter, you can add '%(levelname)s' for level name
# eg __main__ in the log
formatter = logging.Formatter('%(levelname)s: %(name)s - %(message)s')
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)
############################################################################




############################################################################
### define global variables
############################################################################

# define CHEMBL_INPUT as the drug file from ChEMBL ('Browse drugs')
# number of drugs should be 10406
CHEMBL_INPUT = 'chembl_drugs.txt'

# define CHEMBL_TARGETS as the target file from ChEMBL ('Browse drug targets')
# number of drugs associated with targets should be 2007
CHEMBL_TARGETS = 'chembl_drugtargets.txt'

# define CHEMBL_UNIPROT as the chemblID/uniprot mapping file
CHEMBL_UNIPROT = 'chembl_uniprot_mapping.txt'

# define TAXA as the list of taxonomy identifiers we are interested in
# e.g. SCHMA (S. Mansoni), SCHHA (S. haematobium), SCHJA (S. japonicum)
TAXA = ['SCHMA', 'SCHHA', 'SCHJA']

# format of CATH domain eg '4.10.400.10'
CATH_FORMAT = re.compile('.*\..*\..*\..*')
############################################################################



############################################################################
### HEADER_TAB_COUNT HELPER FUNCTION
############################################################################
# find specific header in first line of tab-separated file 
# and return column number of the header
def header_tab_count(tab_file, header):
  '''(str)->int
  Read first line of tab separated file tab_file and return column number 
  of header
  >>>column_count("DEVELOPMENT_PHASE")
  3
  '''

  # read just first line of tab_file
  with open(tab_file, 'r') as f:
    first = f.readline()
  # set counter to 0
  col_number = 0
  # loop until word matches the header
  while not first.split("\t")[col_number] == header:
    col_number = col_number + 1
  #debug check
  #logger.debug('the header tab counter works - one loop')
  # return column number
  return col_number
############################################################################




############################################################################
### FILE_TO_LINES HELPER FUNCTION
############################################################################
# read file using readlines approach and return the lines
def file_to_lines(text_file):
  try:
    input_file = open(text_file, 'r')
    lines = input_file.readlines()
    input_file.close()
    #logger.debug('the try/expect loop is working')
    return lines
  except IOError:
    logger.error('The file ' + text_file + ' cannot be found' +
                 ' in the current directory!')
    #this logger exception will print the whole thing
    #logger.exception('whaaaaat we have error')
    logger.warning('The program is aborted.')
    # exit python
    sys.exit()
############################################################################




############################################################################
### SWAP_DIC HELPER FUNCTION
############################################################################
# read tab-separated mapping file with header and return dictionary with 
# second column as key and first column as values - created for the 
# chemblID uniprot mapping file
def swap_dic(tab_file):
  lines = file_to_lines(tab_file)
  swap_dictionary = {}
  counter = 0
  # iterate over lines
  for i in range(1,len(lines)):
    # split tab
    splitline = lines[i].split("\t")
    counter = counter + 1
    #logger.debug(splitline[0])
    # create dictionary, stripping the carriage return
    swap_dictionary[splitline[1].rstrip('\r\n')] = (splitline[0])
  #logger.debug(swap_dictionary)
  return swap_dictionary
############################################################################



############################################################################
### PROCESS_CHEMBL FUNCTION
############################################################################

# in the end we need a dictionary of chembl ids vs uniprot ids
def process_chembl():
  '''read chembl drug input file, filter, get various info and return 
  list of uniprot ids'''
  # open chembldrugs.txt for reading
  lines = file_to_lines(CHEMBL_INPUT)
  logger.info('The total number of drugs listed in the ChEMBL input file is '
              + str(len(lines)-1) + '.')
  # get the headers
  headers = lines[0]
  # remove duplicate spaces
  headersnospace = " ".join(headers.split())
  # print headers list in lowercase
  # print('The headers are: '+headersnospace.lower())

  col_phase = header_tab_count(CHEMBL_INPUT,"DEVELOPMENT_PHASE")
  col_type = header_tab_count(CHEMBL_INPUT,"DRUG_TYPE")
  col_chemblid = header_tab_count(CHEMBL_INPUT,"CHEMBL_ID")
  
  # count the drugs in the 4+1 classes of clinical phase
  # set counters for clinical phases to zero
  phase1 = 0
  phase2 = 0
  phase3 = 0
  phase4 = 0
  phase_unknown =0
  # iterate over rows, excluding the header row
  for i in range(1,len(lines)):
    # tab separate each row
    rowsplit = lines[i].split("\t")
    if (rowsplit[col_phase] == '1'):
      phase1 = phase1 + 1
    elif (rowsplit[col_phase] == '2'):
      phase2 = phase2 + 1
    elif (rowsplit[col_phase] == '3'):
      phase3 = phase3 + 1
    elif (rowsplit[col_phase] == '4'):
      phase4 = phase4 + 1
    else:
      phase_unknown = phase_unknown + 1

  logger.info('The number of drugs in phase 1 is: ' + str(phase1) +
              '; in phase 2 is: ' + str(phase2) + '; in phase 3 is: ' + 
              str(phase3)+'; in phase 4 is: ' + str(phase4) + 
              '; in unknown phase is: ' + str(phase_unknown) + '.')

  # set up empty list to append lines to
  stripped = []
  # look over lines, excluding header
  for y in range(1,len(lines)):
    # tab separate each row
    rowsplit2 = lines[y].split("\t")
    # check if they are phase 4 or unknown
    # can also add phase 3 from here (or rowsplit2[col_phase] == '3')
    if (rowsplit2[col_phase] == '4'): 
      # append the stripped lines to the list
      stripped.append(lines[y])

  # print friendly statement
  logger.info('We are only considering the entries in phase 4' + 
      ', for a total number of '+ str(len(stripped))+' drugs.')
  
  # set counter for small molecules
  small_mol_count = 0
  chembl_filt_list = []
  # loop over, note here there is no header
  for line in stripped:
  #for x in range(len(lines2)):
    # tab separate
    rowsplit3 = line.split("\t")
    #rowsplit3 = lines2[line].split("\t")
    # check if they are small molecules and append chemids to list
    if rowsplit3[col_type] == 'Synthetic Small Molecule':
      # count how many lines we are retaining
      small_mol_count = small_mol_count + 1
      #logger.debug(rowsplit3[col_chemblid])

      # make list of chembl ids we are interested in
      chembl_filt_list.append(rowsplit3[col_chemblid])
    
  logger.info('The number of filtered drugs that are small molecules is ' +
              str(small_mol_count) + '.')
  #logger.debug(chembl_filt_list)

  
  # open the drug targets chembl file and get lines
  drug_targ = file_to_lines(CHEMBL_TARGETS)
  # get column number for two headers we want (chembl ids for mol and targets)
  col_mol_id = header_tab_count(CHEMBL_TARGETS,'MOLECULE_CHEMBL_ID')
  col_targ_id = header_tab_count(CHEMBL_TARGETS,'TARGET_CHEMBL_ID')
  # empty list in which to store the target chembl ids
  targets_ids = []

  #logger.debug(drug_targ[0])

  # list of target chemblids that refer to the drugs we are interested in
  # ie. small molecules, late clinical stages
  for line in drug_targ:
    rowsplit = line.split("\t")
    # check if the molecule chembl id is one of the drugs we want
    if rowsplit[col_mol_id] in chembl_filt_list:
      # add the target chembl id to the list
      targets_ids.append(rowsplit[col_targ_id])
  logger.info('The number of drugs that have a ChEMBL target associated ' +
              'to it is ' + str(len(targets_ids)) + '.')

  # create dictionary from the chembl/uniprot mapping file
  # the dictionary will be {'chemblID1':'uniprotid1', etc..}
  chembl_uniprot_map_dic = swap_dic(CHEMBL_UNIPROT)
  #logger.debug(chembl_uniprot_map_dic)

  # empty list in which to store uniprot codes
  target_uniprot = []

  # loop over dictionary and check if the chemblid is in our list
  for key in chembl_uniprot_map_dic:
    if key in targets_ids:
      target_uniprot.append(chembl_uniprot_map_dic[key])

  logger.info('The targets that could be mapped to a UniProt ID are ' +
              str(len(target_uniprot)) + '.')

  #remove duplicates from the list
  target_uniprot = list(set(target_uniprot))

  logger.info('The unique UniProt IDs we obtained are ' +
              str(len(target_uniprot)) + '.')
  #logger.debug(target_uniprot)
  return target_uniprot
############################################################################




############################################################################
### PROCESS_DRUGBANK FUNCTION
############################################################################

# process drugbank file to produce a dictionary of drugs vs uniprot ids
#def process_drugbank():
  # implement function

############################################################################




############################################################################
### UNIPROT_TO_CATH FUNCTION
############################################################################
# return list of CATH domain archictures from uniprot list
def uniprot_to_cath(uniprot_list):
  '''(list of str -> list of str)
  run archindex, return list of CATH domain architecture from list of 
  uniprot values
  '''
  # empty list in which to store domain architecture values
  architect_list = []
  # loop over list of uniprot values
  for uniprot_id in uniprot_list:
    # call archschema on the list
    subprocess.call("./../archSchema/bin/archindex -u " + str(uniprot_id) + 
                  " -maxa 1 -maxs 1 -cath > temp.txt", shell=True)
    # store lines
    lines = file_to_lines('temp.txt')
    #logger.debug(lines)
    for i in range(len(lines)):
      # find line that starts with parent
      if lines[i][0:7] == ':PARENT':
        # take the line after the ':PARENT' and split it
        line_split = lines[i+1].split("\t")
        #logger.debug('the line after is ' + str(line_split))

        # check if there are 'p's and get rid of them
        if "p" in line_split[2]:
          # replace p's with nothing
          line_nops = line_split[2].replace('p','')
        else:
          line_nops = line_split[2]
        
        # check if there are undescores
        if "_" in line_nops:
          undersc_split = line_nops.split("_")
          #logger.debug(undersc_split)
          
          for item in undersc_split:
            # check if the format is CATH one
            #cath_format = re.compile('.*\..*\..*\..*')
            if CATH_FORMAT.match(item):
              architect_list.append(item)

        # this is the case of just one entry, no undescores
        else:
          # check the format is CATH one
          if CATH_FORMAT.match(line_nops):
            architect_list.append(line_nops)


  # rm temp.txt in the end
  # this is the last temp file that overwrote the others
  subprocess.call("rm temp.txt", shell=True)
  
  # eliminate duplicate domain architecture values
  architect_list = list(set(architect_list))
  
  logger.info('We have found ' + str(len(architect_list)) + 
              ' unique CATH domain architectures.')
  logger.debug(architect_list)
  # return the list of unique domain architecture values
  return architect_list
############################################################################




############################################################################
### UNIPROT_TO_PFAM FUNCTION
############################################################################
# return list of pfam domain archictures from uniprot list
def uniprot_to_pfam(uniprot_list):
  '''(list of str -> list of str)
  run archindex, return list of pfam domain architecture from list of 
  uniprot values
  '''
  # empty list in which to store domain architecture values
  architect_list = []
  # set counter for debug
  uniprot_counter = 0
  # loop over list of uniprot values
  for uniprot_id in uniprot_list:
    uniprot_counter = uniprot_counter + 1
    # log the 
    logger.debug('We are processing uniprot n.' + str(uniprot_counter)
                + '(' + str(uniprot_id) + ')..')
    # call archschema on the list
    subprocess.call("./../archSchema/bin/archindex -u " + str(uniprot_id) + 
                  " -maxa 1 -maxs 1 > temp.txt", shell=True)
    # store lines
    lines = file_to_lines('temp.txt')
    #logger.debug(lines)
    for i in range(len(lines)):
      # find line that starts with parent
      if lines[i][0:7] == ':PARENT':
        # take the line after the ':PARENT' and split it
        line_split = lines[i+1].split("\t")
        #logger.debug('the line after is ' + str(line_split))
        # check if there are dots
        if "." in line_split[2]:
          dot_split = line_split[2].split(".")
          #logger.debug(undersc_split)
          
          for item in dot_split:
         
            architect_list.append(item)

        # this is the case of just one entry, no dots
        else:
       
          architect_list.append(line_split[2])
  
  # rm temp.txt in the end
  # this is the last temp file that overwrote the others
  subprocess.call("rm temp.txt", shell=True)
  # remove duplicates
  architect_list = list(set(architect_list))

  logger.info('We have found ' + str(len(architect_list)) + 
              ' unique pfam domain architectures.')
  logger.debug(architect_list)
  return architect_list
############################################################################




############################################################################
### ARCH_TO_UNIPROT FUNCTION
############################################################################
# run archindex, filter for TAXA and find uniprot ids
def arch_to_uniprot(arch_list,flag):
  '''(list of str -> list of str)
  run archindex, return list of uniprot from list of domain
  architecture values applying a filter for TAXA (organism)
  '''
  # empty list in which to store domain uniprot values
  uniprot_list = []
  # loop over list of arch values
  for arch_id in arch_list:
    # iterate over the taxa code list (schisto species)
    for taxa_code in TAXA:
      # call archschema on the list
      subprocess.call("./../archSchema/bin/archindex -p " + str(arch_id) + 
                    " -maxa 1 -maxs 1 " + str(flag) + " -s " + taxa_code + 
                    " > temp.txt", shell=True)
      # store lines
      lines = file_to_lines('temp.txt')
      #logger.debug(temp.txt)

      # get the uniprot values and append them to uniprot_list
      for i in range(len(lines)):
        # find line that starts with parent
        if lines[i][0:7] == ':PARENT':
          # take the line after the ':PARENT' and split it
          line_split = lines[i+1].split("\t")
          
          uniprot_list.append(line_split[0])

  # rm temp.txt in the end
  # this is the last temp file that overwrote the others
  subprocess.call("rm temp.txt", shell=True)

  # remove duplicates from list
  uniprot_list = list(set(uniprot_list))

  logger.info('We have found ' + str(len(uniprot_list)) + 
              ' UniProt IDs of schistosoma proteins' +
              ' (taxonomic identifiers ' + str(TAXA) + ').')

  #logger.debug(uniprot_list)
  #return the list of uniprots
  return uniprot_list
############################################################################


############################################################################
### MAIN FUNCTION
############################################################################

# call process_chembl, 
# TO ADD: call process_drugbank, merge uniprot codes

def main():
  # greeting
  logger.info("Hi there, you are running drug_repo for drug repositioning!" +
              " Let's do some mapping.")

  # get a list of target uniprot from chembl drug file
  uniprot_list = process_chembl()
  
  # get a list of target uniprot from drugbank
  #process_drugbank
  
  # merge the lists, remove duplicates, see how many we end up with
  
  # use this fake uniprot list to test
  # overwrite the list with a small set ['B6DTB2', 'Q4JEY0','P11511']
  #['Q4JEY0', 'P68363', 'P10613', 'P18825', 'Q9UM73', 'E1FVX6']
  uniprot_list = ['Q9UM73','Q4JEY0','P68363']

  # call archindex on uniprot list to retrieve cath domain architectures
  cath_list = uniprot_to_cath(uniprot_list)

  # call archindex on uniprot list to retrieve pfam domain architectures
  pfam_list = uniprot_to_pfam(uniprot_list)

  # call archindex on cath values to find the ones from schisto
  cath_flag = "-cath"
  uniprot_schisto_cath_list = arch_to_uniprot(cath_list, cath_flag)

  # call archindex on pfam values, without the flag
  pfam_flag = ""
  uniprot_schisto_pfam_list = arch_to_uniprot(pfam_list, pfam_flag)

  # merge and rm duplicates
  uniprot_schisto_list = list(
                              set(uniprot_schisto_cath_list)|
                              set(uniprot_schisto_pfam_list))

  logger.debug('The merged UniProt values obtained from CATH and pfam ' +
    'are ' + str(len(uniprot_schisto_list)) + '.')
  logger.debug(uniprot_schisto_list)

############################################################################




############################################################################
### call main function, prevent execution on import
############################################################################
if __name__ == "__main__":
  main()
############################################################################
