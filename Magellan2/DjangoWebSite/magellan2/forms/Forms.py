from django import forms
from DjangoWebSite.utils import QHandler 

class VersionForm (forms.Form):
    """
    A form to encapsulate queries for versions from asgard DB
    """
    v_allowed_int_kw = ("main", "sub", "sub2", "bn", "abn", "hf", "p", "id", "last")
    v_allowed_kw = v_allowed_int_kw + ("nice", "name", "comp","rel")
    
    qv = forms.CharField (required=False, 
                          label="Version Selector", 
                              help_text="""
                              """,)
    qv.doc_ref = "a documentation reference"
    
    def clean_handler (self, qname, allowed_kw, allowed_int_kw = []):
        data = self.cleaned_data[qname]
        data_h = QHandler (data)
            
        d = data_h.pos_keywords
        d.update (data_h.neg_keywords)
        errors = []
        for k in d:
            if not k in allowed_kw : errors.append ("Keyword '%s' is not supported. Use %s"%(k, ", ".join (allowed_kw)))
            if not d[k] : errors.append ("Keyword '%s' needs a value."%k)
            if k in allowed_int_kw:
                try : int (d[k])
                except ValueError:
                    errors.append ("Keyword '%s' needs an int value."%k)
        if errors:
            self._errors[qname] = self.error_class(errors)
            del self.cleaned_data[qname]
        
    def clean (self):
        self.clean_handler ('qv', self.v_allowed_kw, self.v_allowed_int_kw)
        return self.cleaned_data
    
class ScenarioForm (VersionForm):
    sc_allowed_int_kw = ("id", )
    sc_allowed_kw = sc_allowed_int_kw + ("status", "name", "b", "set", "impl", "authors", "owner", "spr", "descr")
    qs = forms.CharField (required=False, 
                                  label="Scenario Selector", 
                              help_text="",)
    # The field used to tell which scenario is displayed
    qsid = forms.IntegerField (widget=forms.HiddenInput (), required=False)
    
    def clean (self):
        super (ScenarioForm, self).clean ()
        self.clean_handler ('qs', self.sc_allowed_kw, self.sc_allowed_int_kw)
        return self.cleaned_data
    
class GraphForm (ScenarioForm): 
    """
    A form that is used to select which graphs to show.
    It contains the version selector, the scenario selector, the label and column selector.
    New: it also contains a version reference selector. 
    """
    label_allowed_kw = ("name",)
    column_allowed_kw = ("name",)
    ql = forms.CharField (required=False, 
                              label="Label Selector", 
                              help_text="",)
    qc = forms.CharField (required=False, 
                              label="Column Selector", 
                              help_text="",)
    qbase = forms.CharField (required=False, 
                          label="Baseline version", 
                              help_text="",)

    def clean (self):
        """Very simple at the moment """
        super (GraphForm, self).clean ()
        self.clean_handler ('ql', self.label_allowed_kw)
        self.clean_handler ('qc', self.column_allowed_kw)
        self.clean_handler ('qbase', self.v_allowed_kw, self.v_allowed_int_kw)
        return self.cleaned_data

class ShortcutForm(forms.Form):
    pass

class OverviewForm(ScenarioForm):
    """
    Needed for the overview page.
    """

    qbase = forms.CharField (required=False,
                          label="Baseline version",
                              help_text="",)

    def clean (self):
        super (OverviewForm, self).clean ()
        self.clean_handler ('qbase', self.v_allowed_kw, self.v_allowed_int_kw)
        return self.cleaned_data

class AlertForm(ScenarioForm): 
    """
    A form that is used to select which graphs to show.
    It contains the version selector, the scenario selector, the label and column selector.
    New: it also contains a version reference selector. 
    """
    label_allowed_kw = ("name",)
    column_allowed_kw = ("name",)
    ql = forms.CharField (required=False, 
                              label="Label", 
                              help_text="",)
    qc = forms.CharField (required=False, 
                              label="Column", 
                              help_text="",)
    tolerance = forms.CharField (required=False, 
                          label="Tolerance", 
                              help_text="",)

    def clean (self):
        """Very simple at the moment """
        super (AlertForm, self).clean ()
        self.clean_handler ('ql', self.label_allowed_kw)
        self.clean_handler ('qc', self.column_allowed_kw)
        self.clean_handler ('qbase', self.v_allowed_kw, self.v_allowed_int_kw)
        return self.cleaned_data
