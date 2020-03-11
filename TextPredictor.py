import sys
import os
import tkinter
import re

try:
    from tkinter import StringVar, Entry, Frame, Listbox, Scrollbar
    from Tkconstants import *
except ImportError:
    from tkinter import StringVar, Entry, Frame, Listbox, Scrollbar
    from tkinter.constants import *


def autoscroll(sbar, first, last):
    """Hide and show scrollbar as needed."""
    first, last = float(first), float(last)
    if first <= 0 and last >= 1:
        sbar.grid_remove()
    else:
        sbar.grid()
    sbar.set(first, last)


class Combobox_Autocomplete(Entry, object):
    def __init__(self, master, list_of_items=None, autocomplete_function=None, listbox_width=None, listbox_height=7,
                 ignorecase_match=False, startswith_match=True, vscrollbar=True, hscrollbar=True, **kwargs):
        if hasattr(self, "autocomplete_function"):
            if autocomplete_function is not None:
                raise ValueError("Autocomplete subclass has 'autocomplete_function' implemented")
        else:
            if autocomplete_function is not None:
                self.autocomplete_function = autocomplete_function
            else:
                if list_of_items is None:
                    raise ValueError("If not guiven complete function, list_of_items can't be 'None'")

                if ignorecase_match:
                    if startswith_match:
                        def matches_function(entry_data, item):
                            return item.startswith(entry_data)
                    else:
                        def matches_function(entry_data, item):
                            return item in entry_data

                    self.autocomplete_function = lambda entry_data: [item for item in self.list_of_items if
                                                                     matches_function(entry_data, item)]
                else:
                    if startswith_match:
                        def matches_function(escaped_entry_data, item):
                            if re.match(escaped_entry_data, item, re.IGNORECASE):
                                return True
                            else:
                                return False
                    else:
                        def matches_function(escaped_entry_data, item):
                            if re.search(escaped_entry_data, item, re.IGNORECASE):
                                return True
                            else:
                                return False

                    def autocomplete_function(entry_data):
                        escaped_entry_data = re.escape(entry_data)
                        return [item for item in self.list_of_items if matches_function(escaped_entry_data, item)]

                    self.autocomplete_function = autocomplete_function

        self._listbox_height = int(listbox_height)
        self._listbox_width = listbox_width

        self.list_of_items = list_of_items

        self._use_vscrollbar = vscrollbar
        self._use_hscrollbar = hscrollbar

        kwargs.setdefault("background", "white")

        if "textvariable" in kwargs:
            self._entry_var = kwargs["textvariable"]
        else:
            self._entry_var = kwargs["textvariable"] = StringVar()

        Entry.__init__(self, master, **kwargs)

        self._trace_id = self._entry_var.trace('w', self._on_change_entry_var)

        self._listbox = None

        self.bind("<Tab>", self._on_tab)
        self.bind("<Up>", self._previous)
        self.bind("<Down>", self._next)
        self.bind('<Control-n>', self._next)
        self.bind('<Control-p>', self._previous)

        self.bind("<Return>", self._update_entry_from_listbox)
        self.bind("<Escape>", lambda event: self.unpost_listbox())

    def _on_tab(self, event):
        self.post_listbox()
        return "break"

    def _on_change_entry_var(self, name, index, mode):

        entry_data = self._entry_var.get()

        if entry_data == '':
            self.unpost_listbox()
            self.focus()
        else:
            values = self.autocomplete_function(entry_data)
            if values:
                if self._listbox is None:
                    self._build_listbox(values)
                else:
                    self._listbox.delete(0, END)

                    height = min(self._listbox_height, len(values))
                    self._listbox.configure(height=height)

                    for item in values:
                        self._listbox.insert(END, item)

            else:
                self.unpost_listbox()
                self.focus()

    def _build_listbox(self, values):
        listbox_frame = Frame()

        self._listbox = Listbox(listbox_frame, background="white", selectmode=SINGLE, activestyle="none",
                                exportselection=False)
        self._listbox.grid(row=0, column=0, sticky=N + E + W + S)

        self._listbox.bind("<ButtonRelease-1>", self._update_entry_from_listbox)
        self._listbox.bind("<Return>", self._update_entry_from_listbox)
        self._listbox.bind("<Escape>", lambda event: self.unpost_listbox())

        self._listbox.bind('<Control-n>', self._next)
        self._listbox.bind('<Control-p>', self._previous)

        if self._use_vscrollbar:
            vbar = Scrollbar(listbox_frame, orient=VERTICAL, command=self._listbox.yview)
            vbar.grid(row=0, column=1, sticky=N + S)

            self._listbox.configure(yscrollcommand=lambda f, l: autoscroll(vbar, f, l))

        if self._use_hscrollbar:
            hbar = Scrollbar(listbox_frame, orient=HORIZONTAL, command=self._listbox.xview)
            hbar.grid(row=1, column=0, sticky=E + W)

            self._listbox.configure(xscrollcommand=lambda f, l: autoscroll(hbar, f, l))

        listbox_frame.grid_columnconfigure(0, weight=1)
        listbox_frame.grid_rowconfigure(0, weight=1)

        x = -self.cget("borderwidth") - self.cget("highlightthickness")
        y = self.winfo_height() - self.cget("borderwidth") - self.cget("highlightthickness")

        if self._listbox_width:
            width = self._listbox_width
        else:
            width = self.winfo_width()

        listbox_frame.place(in_=self, x=x, y=y, width=width)

        height = min(self._listbox_height, len(values))
        self._listbox.configure(height=height)

        for item in values:
            self._listbox.insert(END, item)

    def post_listbox(self):
        if self._listbox is not None: return

        entry_data = self._entry_var.get()
        if entry_data == '': return

        values = self.autocomplete_function(entry_data)
        if values:
            self._build_listbox(values)

    def unpost_listbox(self):
        if self._listbox is not None:
            self._listbox.master.destroy()
            self._listbox = None

    def get_value(self):
        return self._entry_var.get()

    def set_value(self, text, close_dialog=False):
        self._set_var(text)

        if close_dialog:
            self.unpost_listbox()

        self.icursor(END)
        self.xview_moveto(1.0)

    def _set_var(self, text):
        self._entry_var.trace_vdelete("w", self._trace_id)
        self._entry_var.set(text)
        self._trace_id = self._entry_var.trace('w', self._on_change_entry_var)

    def _update_entry_from_listbox(self, event):
        if self._listbox is not None:
            current_selection = self._listbox.curselection()

            if current_selection:
                text = self._listbox.get(current_selection)
                self._set_var(text)

            self._listbox.master.destroy()
            self._listbox = None

            self.focus()
            self.icursor(END)
            self.xview_moveto(1.0)

        return "break"

    def _previous(self, event):
        if self._listbox is not None:
            current_selection = self._listbox.curselection()

            if len(current_selection) == 0:
                self._listbox.selection_set(0)
                self._listbox.activate(0)
            else:
                index = int(current_selection[0])
                self._listbox.selection_clear(index)

                if index == 0:
                    index = END
                else:
                    index -= 1

                self._listbox.see(index)
                self._listbox.selection_set(first=index)
                self._listbox.activate(index)

        return "break"

    def _next(self, event):
        if self._listbox is not None:

            current_selection = self._listbox.curselection()
            if len(current_selection) == 0:
                self._listbox.selection_set(0)
                self._listbox.activate(0)
            else:
                index = int(current_selection[0])
                self._listbox.selection_clear(index)

                if index == self._listbox.size() - 1:
                    index = 0
                else:
                    index += 1

                self._listbox.see(index)
                self._listbox.selection_set(index)
                self._listbox.activate(index)
        return "break"


import pandas as pd

word_list = pd.read_csv(r"word.txt", sep='\t')
list_of_items = word_list.a.astype(str)
import re


def generate_ngrams(list_of_items, n):
    ngrams = zip(*[list_of_items[i:] for i in range(n)])
    return [" ".join(ngram) for ngram in ngrams]


list_of_items = generate_ngrams(list_of_items, n=1)
list_of_items
['A',
 'AA',
 'aa',
 'AAA',
 'aaa',
 'AAAA',
 'AAAAAA',
 'AAAL',
 'AAAS',
 'Aaberg',
 'Aachen',
 'AAE',
 'AAEE',
 'AAF',
 'AAG',
 'aah',
 'aahed',
 'aahing',
 'aahs',
 'AAII',
 'aal',
 'Aalborg',
 'Aalesund',
 'aalii',
 'aaliis',
 'aals',
 'Aalst',
 'Aalto',
 'AAM',
 'aam',
 'AAMSI',
 'Aandahl',
 'AandR',
 'Aani',
 'AAO',
 'AAP',
 'AAPSS',
 'Aaqbiye',
 'Aar',
 'Aara',
 'Aarau',
 'AARC',
 'aardvark',
 'aardvarks',
 'aardwolf',
 'aardwolves',
 'Aaren',
 'Aargau',
 'aargh',
 'Aarhus',
 'Aarika',
 'Aaron',
 'aaron',
 'Aaronic',
 'aaronic',
 'Aaronical',
 'Aaronite',
 'Aaronitic',
 'Aaronsbeard',
 'Aaronsburg',
 'Aaronson',
 'AARP',
 'aarrgh',
 'aarrghh',
 'Aaru',
 'AAS',
 'aas',
 'Aasia',
 'aasvogel',
 'aasvogels',
 'AAU',
 'AAUP',
 'AAUW',
 'AAVSO',
 'AAX',
 'Aaxes',
 'Aaxis',
 'AB',
 'AB',
 'Ab',
 'ab',
 'ab',
 'ABA',
 'ABA',
 'Aba',
 'aba',
 'Ababa',
 'Ababdeh',
 'Ababua',
 'abac',
 'abaca',
 'abacas',
 'abacate',
 'abacaxi',
 'abacay',
 'abaci',
 'abacinate',
 'abacination',
 'abacisci',
 'abaciscus',
 'abacist',
 'aback',
 'abacli',
 'Abaco',
 'abacot',
 'abacterial',
 'abactinal',
 'abactinally',
 'abaction',
 'abactor',
 'abaculi',
 'abaculus',
 'abacus',
 'abacuses',
 'Abad',
 'abada',
 'Abadan',
 'Abaddon',
 'abaddon',
 'abadejo',
 'abadengo',
 'abadia',
 'Abadite',
 'abaff',
 'abaft',
 'Abagael',
 'Abagail',
 'Abagtha',
 'Abailard',
 'abaisance',
 'abaised',
 'abaiser',
 'abaisse',
 'abaissed',
 'abaka',
 'Abakan',
 'abakas',
 'Abakumov',
 'abalation',
 'abalienate',
 'abalienated',
 'abalienating',
 'abalienation',
 'abalone',
 'abalones',
 'Abama',
 'abamp',
 'abampere',
 'abamperes',
 'abamps',
 'Abana',
 'aband',
 'abandon',
 'abandonable',
 'abandoned',
 'abandonedly',
 'abandonee',
 'abandoner',
 'abandoners',
 'abandoning',
 'abandonment',
 'abandonments',
 'abandons',
 'abandum',
 'abanet',
 'abanga',
 'Abanic',
 'abannition',
 'Abantes',
 'abapical',
 'abaptiston',
 'abaptistum',
 'Abarambo',
 'Abarbarea',
 'Abaris',
 'abarthrosis',
 'abarticular',
 'abarticulation',
 'Abas',
 'abas',
 'abase',
 'abased',
 'abasedly',
 'abasedness',
 'abasement',
 'abasements',
 'abaser',
 'abasers',
 'abases',
 'Abasgi',
 'abash',
 'abashed',
 'abashedly',
 'abashedness',
 'abashes',
 'abashing',
 'abashless',
 'abashlessly',
 'abashment',
 'abashments',
 'abasia',
 'abasias',
 'abasic',
 'abasing',
 'abasio',
 'abask',
 'abassi',
 'Abassieh',
 'Abassin',
 'abastard',
 'abastardize',
 'abastral',
 'abatable',
 'abatage',
 'Abate',
 'abate',
 'abated',
 'abatement',
 'abatements',
 'abater',
 'abaters',
 'abates',
 'abatic',
 'abating',
 'abatis',
 'abatised',
 'abatises',
 'abatjour',
 'abatjours',
 'abaton',
 'abator',
 'abators',
 'ABATS',
 'abattage',
 'abattis',
 'abattised',
 'abattises',
 'abattoir',
 'abattoirs',
 'abattu',
 'abattue',
 'Abatua',
 'abature',
 'abaue',
 'abave',
 'abaxial',
 'abaxile',
 'abay',
 'abayah',
 'abaze',
 'abb',
 'Abba',
 'abba',
 'abbacies',
 'abbacomes',
 'abbacy',
 'Abbadide',
 'Abbai',
 'abbandono',
 'abbas',
 'abbasi',
 'Abbasid',
 'abbasid',
 'abbassi',
 'Abbassid',
 'Abbasside',
 'Abbate',
 'abbate',
 'abbatial',
 'abbatical',
 'abbatie',
 'abbaye',
 'Abbe',
 'abbe',
 'abbes',
 'abbess',
 'abbesses',
 'abbest',
 'Abbevilean',
 'Abbeville',
 'Abbevillian',
 'abbevillian',
 'Abbey',
 'abbey',
 'abbeys',
 'abbeystead',
 'abbeystede',
 'Abbi',
 'Abbie',
 'abboccato',
 'abbogada',
 'Abbot',
 'abbot',
 'abbotcies',
 'abbotcy',
 'abbotnullius',
 'abbotric',
 'abbots',
 'Abbotsen',
 'Abbotsford',
 'abbotship',
 'abbotships',
 'Abbotson',
 'Abbotsun',
 'Abbott',
 'abbott',
 'Abbottson',
 'Abbottstown',
 'Abboud',
 'abbozzo',
 'ABBR',
 'abbr',
 'abbrev',
 'abbreviatable',
 'abbreviate',
 'abbreviated',
 'abbreviately',
 'abbreviates',
 'abbreviating',
 'abbreviation',
 'abbreviations',
 'abbreviator',
 'abbreviators',
 'abbreviatory',
 'abbreviature',
 'abbroachment',
 'Abby',
 'abby',
 'Abbye',
 'Abbyville',
 'ABC',
 'abc',
 'abcess',
 'abcissa',
 'abcoulomb',
 'ABCs',
 'abd',
 'abdal',
 'abdali',
 'abdaria',
 'abdat',
 'Abdel',
 'AbdelKadir',
 'AbdelKrim',
 'Abdella',
 'Abderhalden',
 'Abderian',
 'Abderite',
 'Abderus',
 'abdest',
 'Abdias',
 'abdicable',
 'abdicant',
 'abdicate',
 'abdicated',
 'abdicates',
 'abdicating',
 'abdication',
 'abdications',
 'abdicative',
 'abdicator',
 'Abdiel',
 'abditive',
 'abditory',
 'abdom',
 'abdomen',
 'abdomens',
 'abdomina',
 'abdominal',
 'Abdominales',
 'abdominales',
 'abdominalia',
 'abdominalian',
 'abdominally',
 'abdominals',
 'abdominoanterior',
 'abdominocardiac',
 'abdominocentesis',
 'abdominocystic',
 'abdominogenital',
 'abdominohysterectomy',
 'abdominohysterotomy',
 'abdominoposterior',
 'abdominoscope',
 'abdominoscopy',
 'abdominothoracic',
 'abdominous',
 'abdominouterotomy',
 'abdominovaginal',
 'abdominovesical',
 'Abdon',
 'Abdu',
 'abduce',
 'abduced',
 'abducens',
 'abducent',
 'abducentes',
 'abduces',
 'abducing',
 'abduct',
 'abducted',
 'abducting',
 'abduction',
 'abductions',
 'abductor',
 'abductores',
 'abductors',
 'abducts',
 'Abdul',
 'AbdulAziz',
 'Abdulbaha',
 'Abdulla',
 'Abe',
 'abe',
 'abeam',
 'abear',
 'abearance',
 'Abebi',
 'abecedaire',
 'abecedaria',
 'abecedarian',
 'abecedarians',
 'abecedaries',
 'abecedarium',
 'abecedarius',
 'abecedary',
 'abed',
 'abede',
 'abedge',
 'Abednego',
 'abegge',
 'abeigh',
 'ABEL',
 'Abel',
 'abel',
 'Abelard',
 'abele',
 'abeles',
 'Abelia',
 'Abelian',
 'abelian',
 'Abelicea',
 'Abelite',
 'abelite',
 'Abell',
 'Abelmoschus',
 'abelmosk',
 'abelmosks',
 'abelmusk',
 'Abelonian',
 'Abelson',
 'abeltree',
 'Abencerrages',
 'abend',
 'abends',
 'Abenezra',
 'abenteric',
 'Abeokuta',
 'abepithymia',
 'ABEPP',
 'Abercrombie',
 'Abercromby',
 'Aberdare',
 'aberdavine',
 'Aberdeen',
 'aberdeen',
 'Aberdeenshire',
 'aberdevine',
 'Aberdonian',
 'aberduvine',
 'Aberfan',
 'Aberglaube',
 'Aberia',
 'Abernant',
 'Abernathy',
 'abernethy',
 'Abernon',
 'aberr',
 'aberrance',
 'aberrancies',
 'aberrancy',
 'aberrant',
 'aberrantly',
 'aberrants',
 'aberrate',
 'aberrated',
 'aberrating',
 'aberration',
 'aberrational',
 'aberrations',
 'aberrative',
 'aberrator',
 'aberrometer',
 'aberroscope',
 'Abert',
 'aberuncate',
 'aberuncator',
 'Aberystwyth',
 'abesse',
 'abessive',
 'abet',
 'abetment',
 'abetments',
 'abets',
 'abettal',
 'abettals',
 'abetted',
 'abetter',
 'abetters',
 'abetting',
 'abettor',
 'abettors',
 'Abeu',
 'abevacuation',
 'Abey',
 'abey',
 'abeyance',
 'abeyances',
 'abeyancies',
 'abeyancy',
 'abeyant',
 'abfarad',
 'abfarads',
 'ABFM',
 'Abgatha',
 'ABHC',
 'abhenries',
 'abhenry',
 'abhenrys',
 'abhinaya',
 'abhiseka',
 'abhominable',
 'abhor',
 'abhorred',
 'abhorrence',
 'abhorrences',
 'abhorrency',
 'abhorrent',
 'abhorrently',
 'abhorrer',
 'abhorrers',
 'abhorrible',
 'abhorring',
 'abhors',
 'Abhorson',
 'ABI',
 'Abia',
 'Abiathar',
 'Abib',
 'abib',
 'abichite',
 'abidal',
 'abidance',
 'abidances',
 'abidden',
 'abide',
 'abided',
 'abider',
 'abiders',
 'abides',
 'abidi',
 'abiding',
 'abidingly',
 'abidingness',
 'Abidjan',
 'Abie',
 'abied',
 'abiegh',
 'abience',
 'abient',
 'Abies',
 'abies',
 'abietate',
 'abietene',
 'abietic',
 'abietin',
 'Abietineae',
 'abietineous',
 'abietinic',
 'abietite',
 'Abiezer',
 'Abigael',
 'Abigail',
 'abigail',
 'abigails',
 'abigailship',
 'Abigale',
 'abigeat',
 'abigei',
 'abigeus',
 'Abihu',
 'Abijah',
 'abilao',
 'Abilene',
 'abilene',
 'abiliment',
 'abilitable',
 'abilities',
 'ability',
 'ability',
 'abilla',
 'abilo',
 'Abilyne',
 'abime',
 'Abimelech',
 'Abineri',
 'Abingdon',
 'Abinger',
 'Abington',
 'Abinoam',
 'Abinoem',
 'abintestate',
 'abiogeneses',
 'abiogenesis',
 'abiogenesist',
 'abiogenetic',
 'abiogenetical',
 'abiogenetically',
 'abiogenist',
 'abiogenous',
 'abiogeny',
 'abiological',
 'abiologically',
 'abiology',
 'abioses',
 'abiosis',
 'abiotic',
 'abiotical',
 'abiotically',
 'abiotrophic',
 'abiotrophy',
 'Abipon',
 'Abiquiu',
 'abir',
 'abirritant',
 'abirritate',
 'abirritated',
 'abirritating',
 'abirritation',
 'abirritative',
 'Abisag',
 'Abisha',
 'Abishag',
 'Abisia',
 'abiston',
 'abit',
 'Abitibi',
 'Abiu',
 'abiuret',
 'Abixah',
 'abject',
 'abjectedness',
 'abjection',
 'abjections',
 'abjective',
 'abjectly',
 'abjectness',
 'abjectnesses',
 'abjoint',
 'abjudge',
 'abjudged',
 'abjudging',
 'abjudicate',
 'abjudicated',
 'abjudicating',
 'abjudication',
 'abjudicator',
 'abjugate',
 'abjunct',
 'abjunction',
 'abjunctive',
 'abjuration',
 'abjurations',
 'abjuratory',
 'abjure',
 'abjured',
 'abjurement',
 'abjurer',
 'abjurers',
 'abjures',
 'abjuring',
 'abkar',
 'abkari',
 'abkary',
 'Abkhas',
 'Abkhasia',
 'Abkhasian',
 'Abkhaz',
 'Abkhazia',
 'Abkhazian',
 'abl',
 'abl',
 'ablach',
 'ablactate',
 'ablactated',
 'ablactating',
 'ablactation',
 'ablaqueate',
 'ablare',
 'Ablast',
 'ablastemic',
 'ablastin',
 'ablastous',
 'ablate',
 'ablated',
 'ablates',
 'ablating',
 'ablation',
 'ablations',
 'ablatitious',
 'ablatival',
 'ablative',
 'ablatively',
 'ablatives',
 'ablator',
 'ablaut',
 'ablauts',
 'ablaze',
 'able',
 'able',
 'ablebodied',
 'ablebodiedness',
 'ableeze',
 'ablegate',
 'ablegates',
 'ablegation',
 'ableminded',
 'ablemindedness',
 'ablend',
 'ableness',
 'ablepharia',
 'ablepharon',
 'ablepharous',
 'Ablepharus',
 'ablepsia',
 'ablepsy',
 'ableptical',
 'ableptically',
 'abler',
 'ables',
 'ablesse',
 'ablest',
 'ablet',
 'ablewhackets',
 'ablings',
 'ablins',
 'ablock',
 'abloom',
 'ablow',
 'ABLS',
 'ablude',
 'abluent',
 'abluents',
 'ablush',
 'ablute',
 'abluted',
 'ablution',
 'ablutionary',
 'ablutions',
 'abluvion',
 'ably',
 'ably',
 'ABM',
 'abmho',
 'abmhos',
 'abmodalities',
 'abmodality',
 'abn',
 'Abnaki',
 'Abnakis',
 'abnegate',
 'abnegated',
 'abnegates',
 'abnegating',
 'abnegation',
 'abnegations',
 'abnegative',
 'abnegator',
 'abnegators',
 'Abner',
 'abner',
 'abnerval',
 'abnet',
 'abneural',
 'abnormal',
 'abnormalcies',
 'abnormalcy',
 'abnormalise',
 'abnormalised',
 'abnormalising',
 'abnormalism',
 'abnormalist',
 'abnormalities',
 'abnormality',
 'abnormalize',
 'abnormalized',
 'abnormalizing',
 'abnormally',
 'abnormalness',
 'abnormals',
 'abnormities',
 'abnormity',
 'abnormous',
 'abnumerable',
 'Abo',
 'abo',
 'aboard',
 'aboardage',
 'Abobra',
 'abococket',
 'abodah',
 'abode',
 'aboded',
 'abodement',
 'abodes',
 'aboding',
 'abody',
 'abogado',
 'abogados',
 'abohm',
 'abohms',
 'aboideau',
 'aboideaus',
 'aboideaux',
 'aboil',
 'aboiteau',
 'aboiteaus',
 'aboiteaux',
 'abolete',
 'abolish',
 'abolishable',
 'abolished',
 'abolisher',
 'abolishers',
 'abolishes',
 'abolishing',
 'abolishment',
 'abolishments',
 'abolition',
 'abolitionary',
 'abolitionise',
 'abolitionised',
 'abolitionising',
 'abolitionism',
 'abolitionist',
 'abolitionists',
 'abolitionize',
 'abolitionized',
 'abolitionizing',
 'abolitions',
 'abolla',
 'abollae',
 'aboma',
 'abomas',
 'abomasa',
 'abomasal',
 'abomasi',
 'abomasum',
 'abomasus',
 'abomasusi',
 'Abomb',
 'abomb',
 'abominability',
 'abominable',
 'abominableness',
 'abominably',
 'abominate',
 'abominated',
 'abominates',
 'abominating',
 'abomination',
 'abominations',
 'abominator',
 'abominators',
 'abomine',
 'abondance',
 'Abongo',
 'abonne',
 'abonnement',
 'aboon',
 'aborad',
 'aboral',
 'aborally',
 'abord',
 'Aboriginal',
 'aboriginal',
 'aboriginality',
 'aboriginally',
 'aboriginals',
 'aboriginary',
 'Aborigine',
 'aborigine',
 'aborigines',
 'Abormiri',
 'Aborn',
 'aborning',
 'aborning',
 'aborsement',
 'aborsive',
 'abort',
 'aborted',
 'aborter',
 'aborters',
 'aborticide',
 'abortient',
 'abortifacient',
 'abortin',
 'aborting',
 'abortion',
 'abortional',
 'abortionist',
 'abortionists',
 'abortions',
 'abortive',
 'abortively',
 'abortiveness',
 'abortogenic',
 'aborts',
 'abortus',
 'abortuses',
 'abos',
 'abote',
 'Abott',
 'abouchement',
 'aboudikro',
 'abought',
 'Aboukir',
 'aboulia',
 'aboulias',
 'aboulic',
 'abound',
 'abounded',
 'abounder',
 'abounding',
 'aboundingly',
 'abounds',
 'Abourezk',
 'about',
 'aboutface',
 'aboutfaced',
 'aboutfacing',
 'abouts',
 'aboutship',
 'aboutshipped',
 'aboutshipping',
 'aboutsledge',
 'aboutturn',
 'above',
 'aboveboard',
 'aboveboard',
 'abovecited',
 'abovedeck',
 'abovefound',
 'abovegiven',
 'aboveground',
 'abovementioned',
 'abovementioned',
 'abovenamed',
 'aboveproof',
 'abovequoted',
 'abovereported',
 'aboves',
 'abovesaid',
 'abovesaid',
 'abovestairs',
 'abovewater',
 'abovewritten',
 'abow',
 'abox',
 'Abp',
 'abp',
 'ABPC',
 'Abqaiq',
 'abr',
 'abr',
 'Abra',
 'abracadabra',
 'abrachia',
 'abrachias',
 'abradable',
 'abradant',
 'abradants',
 'abrade',
 'abraded',
 'abrader',
 'abraders',
 'abrades',
 'abrading',
 'Abraham',
 'abraham',
 'Abrahamic',
 'Abrahamidae',
 'Abrahamite',
 'Abrahamitic',
 'Abrahamman',
 'abrahamman',
 'Abrahams',
 'Abrahamsen',
 'Abrahan',
 'abraid',
 ...]
if __name__ == '__main__':
    try:
        from Tkinter import Tk
    except ImportError:
        from tkinter import Tk

    list_of_items
    root = Tk()
    root.geometry("300x200")

    combobox_autocomplete = Combobox_Autocomplete(root, list_of_items, highlightthickness=1)
    combobox_autocomplete.pack()

    combobox_autocomplete.focus()

    root.mainloop()


