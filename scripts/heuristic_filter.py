import os
import sys
import pylogg as log

from collections import defaultdict

from backend import postgres, sett
from backend.postgres.orm import Papers, FilteredPapers, PaperTexts, FilteredParagraphs, PropertyMetadata

import pranav.prompt_extraction.config
from pranav.prompt_extraction.run_inference import RunInformationExtraction
from pranav.prompt_extraction.parse_args import parse_args
from pranav.prompt_extraction.utils import connect_remote_database, LoadNormalizationDataset, ner_feed
from pranav.prompt_extraction.pre_processing import PreProcessor
from pranav.prompt_extraction.run_inference import RunInformationExtraction

import json
import torch    

from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline

sett.load_settings()
postgres.load_settings()
db = postgres.connect()

# class HeuristicFilter(RunInformationExtraction):
# 	def __init__(self, args):
# 		super(HeuristicFilter, self).__init__(args=args)


material_entity_types = ['POLYMER', 'POLYMER_FAMILY', 'MONOMER', 'ORGANIC']

filtration_dict = defaultdict(int)



def add_to_filtered_paragrahs(para, filter_name):
	paragraph = FilteredParagraphs().get_one(db, {'para_id': para.id, 'filter_name': filter_name})
	if paragraph is not None:
		log.trace(f"Paragraph in PostGres: {para.id}. Skipped.")
		return False
	
	else:
		obj = FilteredParagraphs()
		obj.para_id = para.id
		obj.filter_name = filter_name
		obj.insert(db)

		log.trace(f"Added to PostGres: {para.id}")

		return True
			

	
def heuristic_filter_check(property:str, publisher_directory:str, filter_name:str):
	mode = property.replace(" ", "_")
	filter_name = filter_name

	prop_metadata = PropertyMetadata().get_one(db, {"name": property})
	keyword_list = prop_metadata.other_names

	#extract all paragraphs from polymer DOIs belonging to a particular publisher 
	poly_entries =  (db.query(FilteredPapers)
							.join(Papers, FilteredPapers.doi == Papers.doi)
							.filter(Papers.directory == publisher_directory)
							.order_by(FilteredPapers.id)
							.all())

	poly_dois = [entry.doi for entry in poly_entries]

	log.info(f'Number of documents belonging to publisher {publisher_directory}: {len(poly_dois)}')

	relevant_paras = 0
	for doi in poly_dois:

		if sett.Run.debugCount >0:
			if filtration_dict['total_dois'] > sett.Run.debugCount:
				break
			
		log.trace(f"Processing {doi}")
		filtration_dict['total_dois'] +=1

		paragraphs = PaperTexts().get_all(db, {'doi': doi})
		log.trace(f'Number of paragraphs found: {len(paragraphs)}')

		relevant_doi_paras = 0

		#para entry has correspondinf id and text
		for para in paragraphs:
			filtration_dict['total_paragraphs'] +=1
			found = process_property(mode= mode,keyword_list=keyword_list, para= para, 
														prop_metadata=prop_metadata, ner_filter=False, heuristic_filter=True)
			
			if found:
				log.warn(f"{para.id} passed the heuristic filter ")
				relevant_paras +=1
				relevant_doi_paras +=1

				if add_to_filtered_paragrahs(para=para, filter_name = filter_name):
					if relevant_paras % 50 == 0:
						db.commit()
					

			else:
				log.info(f"{para.id} did not pass the heuristic filter")
				# log.trace(para.text)
		
		if relevant_doi_paras>0:
			filtration_dict[f"{mode}_documents"] +=1
			log.note(f'DOI: {doi} contains paragraphs for property: {mode}.')


		if filtration_dict['total_dois']% 100 == 0 or filtration_dict['total_dois']== sett.Run.debugCount:
			log.info(f'Number of total documents: {filtration_dict["total_dois"]}')
			log.info(f'Number of total paragraphs: {filtration_dict["total_paragraphs"]}')
			# log.note(f'Number of relevant documents: {filtration_dict["relevant_documents"]}')
			log.info(f'Number of documents with {property} information: {filtration_dict[f"{mode}_documents"]}')
			log.info(f'Number of paragraphs with {property} keywords: {filtration_dict[f"{mode}_keyword_paragraphs"]}')
			log.info(f'Number of paragraphs with {property} information after NER filter: {filtration_dict[f"{mode}_keyword_paragraphs_ner"]}')
			log.info(f'Last processed para_id: {para.id}')

	db.commit()


def keyword_filter(keyword_list, para):
	"""Pass a filter to only pass paragraphs with relevant information to the LLM"""
	if any([keyword in para.text or keyword in para.text.lower() for keyword in keyword_list]):
		log.warn(f'{para.id} passed the heuristic filter check.')
		return True
	
	return False

def process_property(mode, keyword_list, para, prop_metadata, ner_filter= False, heuristic_filter = True):
	if heuristic_filter:
		if keyword_filter(keyword_list, para):
			filtration_dict[f'{mode}_keyword_paragraphs']+=1
			return True
	# if ner_filter:
	# 	ner_output, ner_filter_output = ner_filter(para, unit_list= prop_metadata.units, ner_output=ner_output)
	# 	if ner_filter_output:
	# 		filtration_dict[f'{mode}_keyword_paragraphs_ner']+=1


# def ner_filter(para, unit_list, ner_output=None):
# 	"""Pass paragraph through NER pipeline to check whether it contains relevant information"""
# 	if ner_output is None:
# 			ner_output = ner_pipeline(para.text)
# 	mat_flag = False
# 	prop_name_flag = False
# 	prop_value_flag = False
# 	for entity in ner_output:
# 			if entity['entity_group'] in material_entity_types:
# 					mat_flag = True
# 			elif entity['entity_group'] == 'PROP_NAME':
# 					prop_name_flag = True
# 			elif entity['entity_group'] == 'PROP_VALUE' and any([entity['word'].endswith(unit.lower()) for unit in unit_list]): # Using ends with to avoid false positives such as K in kPa or °C/min
# 					prop_value_flag = True
			
# 	output_flag = mat_flag and prop_name_flag and prop_value_flag
	
# 	return ner_output, output_flag


def log_run_info(property, publisher_directory):
    """
        Log run information for reference purposes.
        Returns a log Timer.
    """
    t1 = log.note(f"Heuristic Filter Run for property: {property} and publisher: {publisher_directory}")
    log.info("CWD: {}", os.getcwd())
    log.info("Host: {}", os.uname())

    if sett.Run.debugCount > 0:
        log.note("Debug run. Will parse maximum {} files.",
                 sett.Run.debugCount)
    else:
        log.note("Production run. Will parse all files.")

    log.info("Using loglevel = {}", sett.Run.logLevel)

    return t1


if __name__ == '__main__':
	
	publisher_directory = 'rsc'
	property = "thermal decomposition temperature"
	filename = property.replace(" ", "_")
	filter_name = 'property_td'
	
	os.makedirs(sett.Run.directory, exist_ok=True)
	log.setFile(open(sett.Run.directory+f"/hf_{publisher_directory}_{filename}.log", "w+"))
	log.setLevel(sett.Run.logLevel)
	log.setFileTimes(show=True)
	log.setConsoleTimes(show=True)
		
	t1 = log_run_info(property, publisher_directory)
	
	heuristic_filter_check(property= property, publisher_directory= publisher_directory, filter_name=filter_name)
		
	t1.done("All Done.")
