# Copyright (C) 2014, Ugo Pozo
#               2014, Câmara Municipal de São Paulo

# forms.py - formulários utilizado pelo Anubis

# Este arquivo é parte do software Anubis.

# Anubis é um software livre: você pode redistribuí-lo e/ou modificá-lo
# sob os termos da Licença Pública Geral GNU (GNU General Public License),
# tal como é publicada pela Free Software Foundation, na versão 3 da
# licença, ou (sua decisão) qualquer versão posterior.

# Anubis é distribuído na esperança de que seja útil, mas SEM NENHUMA
# GARANTIA; nem mesmo a garantia implícita de VALOR COMERCIAL ou ADEQUAÇÃO
# PARA UM PROPÓSITO EM PARTICULAR. Veja a Licença Pública Geral GNU para
# mais detalhes.

# Você deve ter recebido uma cópia da Licença Pública Geral GNU junto com
# este programa. Se não, consulte <http://www.gnu.org/licenses/>.

from django import forms
from rest_framework import serializers

class FieldSerializer(serializers.Serializer):
    ui_element = serializers.SerializerMethodField('get_ui_element')
    required = serializers.BooleanField()
    label = serializers.CharField()
    label_suffix = serializers.CharField()
    help_text = serializers.CharField()
    choices = serializers.SerializerMethodField('get_choices')
    is_numeric = serializers.SerializerMethodField('get_is_numeric')

    def get_ui_element(self, obj):
        if isinstance(obj, forms.DateField):
            return "DatePicker"
        elif isinstance(obj, forms.ChoiceField):
            return "SelectField"
        else:
            return "TextField"

    def get_choices(self, obj):
        choices = None

        if isinstance(obj, forms.ChoiceField):
            choices = obj.choices

        return choices

    def get_is_numeric(self, obj):
        return isinstance(obj, (forms.IntegerField, forms.FloatField))


class FilterForm(forms.Form):
    pass


class RangeForm(FilterForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.range_fields = []

    def clean(self):
        cleaned_data = super().clean()

        for start_field, end_field in self.range_fields:
            start_value = cleaned_data.get(start_field)
            end_value = cleaned_data.get(end_field)

            if start_value and end_value and end_value < start_value:
                message = "O campo {} deve ter valor maior que o campo {}" \
                    .format(start_field, end_field)
                self.add_error(start_field, message)
                self.add_error(end_field, message)

        return cleaned_data
