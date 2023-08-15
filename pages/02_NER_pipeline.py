import pylogg
import sett
import streamlit as st
from stqdm import stqdm

import frontend.resources as res
from frontend.sidebar import Sidebar
from frontend.upload import Uploader
from frontend.base import Container

from backend.postgres.orm import Papers, PaperSections
from backend.utils.frame import Frame
from backend.data.properties import LLMProperties
from backend.ner_pipeline import RecordExtractor

logger = pylogg.New('test')
G = st.session_state

class Sidebar:
    def __init__(self) -> None:
        self.doi = None
        self.properties = []
        self.property_df = res.selected_properties().get_list()
        self.only_polymers = False
        self.debug = sett.Run.debug

        if not 'doi' in G:
            G.doi = ''

        if not 'next' in G:
            G.next = False

    def show(self):
        logger.debug("Properties: {}", self.property_df.Property)
        with st.sidebar:
           self.doi = st.text_input(label="Select paper", placeholder='doi',
                                    value=G.doi)
           st.button("Next Paper", on_click=self.next_paper)
           self.properties = st.multiselect(
               "Properties",
               options=self.property_df.Property)
           self.only_polymers = st.checkbox(
               "Polymers Only", value=self.only_polymers)
           self.debug = st.checkbox(
               "Debug", value=self.debug)
           
    def next_paper(self):
        print("Next paper ...")
        G.next = True


class Body(Container):
    def __init__(self) -> None:
        super().__init__()

    def top(self):
        #@Todo: does not work
        js = '''
        <script>
            var top = window.parent.document.querySelector("#header");
            top.scrollIntoView(true);
        </script>
        '''
        with self.div:
            st.components.v1.html(js)

    def show(self, paper, side, text_list):
        ner = res.materials_bert()

        with self.div:
            st.header(paper.title, anchor='header')
            st.markdown(f"https://doi.org/{side.doi}")

            selected_props = []
            for prop in side.properties:
                selected_props.append(prop)
                selected_props += res.selected_properties().get_corefs(prop)
            st.write("Looking for properties", selected_props)

            # abstract = paper.abstract
            groups = []

            for para in stqdm(text_list):
                st.markdown(f"[{para.type}] **{para.name}**: {para.text}")
                tags = ner.get_tags(para.text)
                record = RecordExtractor(para.text, tags, debug=side.debug)
                groups = record.extract(only_polymers=side.only_polymers)
                if groups:
                    with st.expander("NER Tags"):
                        st.write(groups)
                    st.write("Polymers:", record.polymers)
                    st.write("Materials:", record.materials)
                    st.write("Properties:", record.properties)
                    st.write("Abbreviations:", record.abbreviations)
                else:
                    st.warning("No extractable data found.")

## Control flow
## -----------------------------------------------------------------------------
def main():
    side = Sidebar()
    upload = Uploader()
    body = Body()

    db = res.postgres()

    text_list = []

    side.show()

    if side.doi:
        paper : Papers = Papers().get_one(
            db, criteria={'doi': side.doi}
        )

        if G.next:
            print("Fetching next...")
            paper : Papers = Papers().get_one(
                db, criteria={'id': paper.id+1}
            )
            G.doi = paper.doi
            G.next = False

        text_list : list[PaperSections] = PaperSections().get_all(
            db, criteria={'doi': side.doi})
        
        
    if not text_list:
        st.info("No paragraphs found. Please enter a new DOI. Or upload a file.")
        upload.show()
    else:
        body.show(paper, side, text_list)


if __name__ == '__main__':
    main()
