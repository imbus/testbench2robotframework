"""Call parameters whose representative is an attachment.

TestBench exports such a file to 'attachments/representatives/DT-<datatype key>/'
inside the report and puts only the file name into the parameter value. The
generated keyword call needs a path Robot can open, so the value becomes
'${ITB_ATTACHMENTS_DIR}/representatives/DT-<key>/<file>' - the variable
points to the report's attachments directory at execution time.
"""

from testbench2robotframework.model import (
    DataTypeSummary,
    KeywordCall,
    KeywordCallSpecification,
    KeywordCallType,
    KindOfDataType,
    ParameterDefinitionType,
    ParameterEvaluationType,
    ParameterSummary,
    ParameterValue,
    RepresentativeType,
    SequencePhase,
)
from testbench2robotframework.testbench2rf import parameter_value

DATATYPE = DataTypeSummary(
    key="6917529030000126275",
    kind=KindOfDataType.Reference,
    name="VorgefertigteNachrichten",
    path="04_Daten",
    uniqueID="DEFAULT-DT-289865",
)
ATTACHMENT_PATH = (
    "${ITB_ATTACHMENTS_DIR}/representatives/DT-6917529030000126275/Vorlage_pain.001.001.09.xml"
)


def parameter(  # noqa: PLR0913
    value, value_type, *, key="870816", name="Vorlage", data_type=None, alias=None
):
    return ParameterSummary(
        definitionType=ParameterDefinitionType.DetailedInstance,
        key=key,
        name=name,
        evaluationType=ParameterEvaluationType.CallByValue,
        dataType=data_type,
        value=value,
        valueType=value_type,
        parameterValue=ParameterValue(name=name, key=alias, dtSequenceKeys=[]) if alias else None,
    )


def keyword_call(name, *parameters, sequence_id="1", parent_id=None, keyword_type=None):
    return KeywordCall(
        sequenceID=sequence_id,
        numbering=sequence_id,
        parentID=parent_id,
        spec=KeywordCallSpecification(
            key="1",
            name=name,
            sequencePhase=SequencePhase.TestStep,
            callType=KeywordCallType.Flow,
            comments="",
            callParameters=list(parameters),
            keywordType=keyword_type,
        ),
    )


def value_of(step, parameter_index=0, steps=()):
    steps_by_id = {candidate.sequenceID: candidate for candidate in (step, *steps)}
    return parameter_value(step.spec.callParameters[parameter_index], step, steps_by_id)


def test_attachment_value_points_into_the_report_attachments():
    step = keyword_call(
        "Vorlage holen",
        parameter("Vorlage_pain.001.001.09.xml", RepresentativeType.Attachment, data_type=DATATYPE),
    )
    assert value_of(step) == ATTACHMENT_PATH


def test_text_value_is_passed_through():
    step = keyword_call(
        "Vorlage holen",
        parameter("Vorlage_pain.001.001.09.xml", RepresentativeType.Text, data_type=DATATYPE),
    )
    assert value_of(step) == "Vorlage_pain.001.001.09.xml"


def test_empty_attachment_value_stays_empty():
    step = keyword_call("Vorlage holen", parameter(None, RepresentativeType.Attachment))
    assert value_of(step) == ""


def test_data_type_is_taken_from_the_calling_keywords_parameter():
    # Inside the compound keyword the atomic call only knows the alias of the
    # parameter it got the value from; the data type sits on the outermost call.
    root = keyword_call(
        "Vorlage holen",
        parameter("Vorlage_pain.001.001.09.xml", RepresentativeType.Attachment, data_type=DATATYPE),
        sequence_id="18",
    )
    compound = keyword_call(
        "Hole Nachrichten Vorlage",
        parameter(
            "Vorlage_pain.001.001.09.xml",
            RepresentativeType.Attachment,
            key="1052933",
            alias="870816",
        ),
        sequence_id="20",
        parent_id="18",
    )
    atomic = keyword_call(
        "Load Message",
        parameter(
            "Vorlage_pain.001.001.09.xml",
            RepresentativeType.Attachment,
            key="340804",
            name="MessageFile",
            alias="1052933",
        ),
        sequence_id="21",
        parent_id="20",
    )
    assert value_of(atomic, steps=(root, compound)) == ATTACHMENT_PATH
    assert value_of(compound, steps=(root,)) == ATTACHMENT_PATH


def test_attachment_without_resolvable_data_type_is_passed_through():
    atomic = keyword_call(
        "Load Message",
        parameter("Vorlage_pain.001.001.09.xml", RepresentativeType.Attachment, alias="unknown"),
        sequence_id="21",
        parent_id="20",
    )
    assert value_of(atomic) == "Vorlage_pain.001.001.09.xml"


def test_custom_variable_name():
    step = keyword_call(
        "Vorlage holen",
        parameter("Vorlage_pain.001.001.09.xml", RepresentativeType.Attachment, data_type=DATATYPE),
    )
    steps_by_id = {step.sequenceID: step}
    value = parameter_value(
        step.spec.callParameters[0], step, steps_by_id, attachments_variable="ATT"
    )
    assert value == "${ATT}/representatives/DT-6917529030000126275/Vorlage_pain.001.001.09.xml"


def test_empty_variable_name_gives_a_path_relative_to_the_report():
    step = keyword_call(
        "Vorlage holen",
        parameter("Vorlage_pain.001.001.09.xml", RepresentativeType.Attachment, data_type=DATATYPE),
    )
    steps_by_id = {step.sequenceID: step}
    value = parameter_value(step.spec.callParameters[0], step, steps_by_id, attachments_variable="")
    assert value == "representatives/DT-6917529030000126275/Vorlage_pain.001.001.09.xml"
