# pylint: skip-file
from __future__ import annotations

from pydantic import BaseModel
from enum import Enum, auto
from typing import List, Optional


class StrEnum(str, Enum):
    def __new__(cls, *args):
        for arg in args:
            if not isinstance(arg, (str, auto)):
                raise TypeError(f"Values of StrEnums must be strings: {repr(arg)} is a {type(arg)}")
        return super().__new__(cls, *args)

    def __str__(self):
        return self.value

    def _generate_next_value_(name, *_):
        return name


class TestFilterType(StrEnum):
    TestTheme = "TestTheme"
    TestCaseSet = "TestCaseSet"
    TestCase = "TestCase"


class TestStructureElementType(StrEnum):
    Root = "Root"
    TestTheme = "TestTheme"
    TestCaseSet = "TestCaseSet"


class Priority(StrEnum):
    Undefined = "Undefined"
    Low = "Low"
    Middle = "Middle"
    High = "High"


class ReferenceType(StrEnum):
    Reference = "Reference"
    Hyperlink = "Hyperlink"
    Attachment = "Attachment"


class SpecStatus(StrEnum):
    NotPlanned = "NotPlanned"
    Planned = "Planned"
    InProgress = "InProgress"
    InReview = "InReview"
    Released = "Released"


class InteractionVerdict(StrEnum):
    Pass = "Pass"
    Fail = "Fail"
    Skipped = "Skipped"
    ToVerify = "ToVerify"
    Warn = "Warn"
    Undefined = "Undefined"
    Blocked = "Blocked"


class VerdictStatus(StrEnum):
    Undefined = "Undefined"
    ToVerify = "ToVerify"
    Fail = "Fail"
    Pass = "Pass"


class ActivityStatus(StrEnum):
    NotPlanned = "NotPlanned"
    Planned = "Planned"
    Assigned = "Assigned"
    Running = "Running"
    Canceled = "Canceled"
    Skipped = "Skipped"
    Performed = "Performed"


class ExecStatus(StrEnum):
    NotBlocked = "NotBlocked"
    Blocked = "Blocked"


class UDFType(StrEnum):
    String = "String"
    Enumeration = "Enumeration"
    Boolean = "Boolean"


class SequencePhase(StrEnum):
    Setup = "Setup"
    TestStep = "TestStep"
    Teardown = "Teardown"


class InteractionCallType(StrEnum):
    Check = "Check"
    Flow = "Flow"


class InteractionType(StrEnum):
    Compound = "Compound"
    Atomic = "Atomic"
    Textual = "Textual"


class ParameterDefinitionType(StrEnum):
    DETAILED = "DETAILED"
    ARRAY = "ARRAY"
    ATOMIC = "ATOMIC"


class ParameterEvaluationType(StrEnum):
    CallByReference = "CallByReference"
    CallByValue = "CallByValue"
    CallByReferenceMandatory = "CallByReferenceMandatory"


class RepresentativeType(StrEnum):
    Text = "Text"
    Placeholder = "Placeholder"
    Attachment = "Attachment"
    Hyperlink = "Hyperlink"
    Reference = "Reference" 


class KindOfDataType(StrEnum):
    Regular = "Regular"
    Reference = "Reference"
    Global = "Global"
    AcceptingGlobal = "AcceptingGlobal"


class ProjectMember(BaseModel):
    userkey: str
    userLogin: str
    userName: str
    projectkey: str
    projectName: str
    roles: List[str]


class ProjectDetails(BaseModel):
    key: str
    creationTime: str
    name: str
    status: str
    visibility: bool
    tovsCount: int
    cyclesCount: int
    description: str
    lockerKey: Optional[int] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None


class TOVDetails(BaseModel):
    key: str
    creationTime: str
    name: str
    status: str
    visibility: bool
    cyclesCount: int
    description: str
    lockerKey: Optional[int] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None


class CycleDetails(BaseModel):
    key: str
    creationTime: str
    name: str
    status: str
    visibility: bool
    description: str
    startDate: Optional[str] = None
    endDate: Optional[str] = None


class UserDetails(BaseModel):
    key: str
    login: str
    name: str
    email: str
    passwordExpired: bool
    active: bool


class UserSummary(BaseModel):
    key: str
    login: str
    name: str
    active: bool


class UserDefinedField(BaseModel):
    key: str
    name: str
    value: str
    udfType: UDFType


class Keyword(BaseModel):
    key: str
    name: str
    isVariantsMarker: bool


class Reference(BaseModel):  # TODO: May be changed. Differs to OpenApi.YML
    type: ReferenceType
    path: str


class UserReference(BaseModel):
    key: str
    name: str


class RequirementReference(BaseModel):
    key: str
    edited: bool


class ConditionSummary(BaseModel):
    key: str
    uniqueID: str
    name: str
    description: str
    version: Optional[str] = None


class TestCaseSetSpecificationSummary(BaseModel):
    key: str
    description: str
    reviewComment: str
    status: SpecStatus
    priority: Priority
    responsible: Optional[UserReference]
    dueDate: Optional[str]
    reviewer: Optional[UserReference]
    udfs: List[UserDefinedField]
    keywords: List[Keyword]
    # references: List[Reference]  #TODO: MUST BE CHANGED IN THE FUTURE AGAIN!!!
    references: List[str]
    requirements: List[RequirementReference]
    preConditions: List[ConditionSummary]
    postConditions: List[ConditionSummary]


class TestCaseSpecificationDetails(BaseModel):
    key: str
    comments: str
    udfs: List[UserDefinedField]
    keywords: List[Keyword]
    requirements: List[RequirementReference]


class TestCaseSetExecutionSummary(BaseModel):
    key: str
    comments: str
    udfs: List[UserDefinedField]
    keywords: List[Keyword]


class TestCaseSpecificationSummary(BaseModel):
    key: str
    comments: str
    requirements: List[RequirementReference]


class TestCaseExecutionSummary(BaseModel):
    key: str
    status: ActivityStatus
    execStatus: ExecStatus
    verdict: VerdictStatus
    comments: str
    defects: List[str]
    tester: Optional[UserReference] = None


class TestCaseSummary(BaseModel):
    uniqueID: str
    index: int
    spec: TestCaseSpecificationSummary
    exec: Optional[TestCaseExecutionSummary] = None


class TestCaseExecutionDetails(BaseModel):
    key: str
    status: ActivityStatus
    execStatus: ExecStatus
    verdict: VerdictStatus
    plannedDuration: int
    actualDuration: int
    currentUser: UserReference
    comments: str  # TODO: Insert htmlComment
    version: Optional[str]
    defects: List[str]
    udfs: List[UserDefinedField]
    keywords: List[Keyword]
    # references: List[Reference]  #TODO: MUST BE CHANGED IN THE FUTURE AGAIN!!!
    references: List[str]
    tester: Optional[UserReference] = None


class TestCaseSetDetails(BaseModel):
    key: str
    numbering: str
    uniqueID: str
    name: str
    spec: TestCaseSetSpecificationSummary
    testCases: List[TestCaseSummary]
    exec: Optional[TestCaseSetExecutionSummary] = None


class InteractionExecutionSummary(BaseModel):
    verdict: InteractionVerdict
    time: str
    duration: int
    currentUser: UserReference
    tester: Optional[UserReference]
    comments: str
    # references: List[Reference]  #TODO: MUST BE CHANGED IN THE FUTURE AGAIN!!!
    references: List[str]


class InteractionSpecificationSummary(BaseModel):
    callKey: str
    sequencePhase: SequencePhase
    callType: InteractionCallType
    description: str
    comments: str
    # references: List[Reference]  #TODO: MUST BE CHANGED IN THE FUTURE AGAIN!!!
    references: List[str]
    preConditions: List[ConditionSummary]
    postConditions: List[ConditionSummary]


class DataTypeSummary(BaseModel):
    key: str
    name: str
    kind: KindOfDataType
    version: Optional[str]
    path: str
    uniqueID: str


class ParameterSummary(BaseModel):
    key: str
    name: str
    value: Optional[str]
    valueType: RepresentativeType
    definitionType: ParameterDefinitionType
    evaluationType: ParameterEvaluationType
    dataType: Optional[DataTypeSummary]


class InteractionDetails(BaseModel):
    key: str
    uniqueID: str
    name: str
    version: Optional[str]
    interactionType: InteractionType
    path: str
    spec: InteractionSpecificationSummary
    exec: Optional[InteractionExecutionSummary]
    parameters: List[ParameterSummary]
    interactions: List[InteractionDetails]


class TestCaseDetails(BaseModel):
    uniqueID: str
    spec: TestCaseSpecificationDetails
    interactions: List[InteractionDetails]
    parameters: List[ParameterSummary]
    exec: Optional[TestCaseExecutionDetails] = None


class TestStructureSpecification(BaseModel):
    key: str
    locker: Optional[UserReference]
    status: SpecStatus


class TestStructureAutomation(BaseModel):
    key: str
    locker: Optional[UserReference]
    status: SpecStatus


class TestStructureExecution(BaseModel):
    key: str
    locker: Optional[UserReference]
    status: ActivityStatus
    execStatus: ExecStatus
    verdict: VerdictStatus


class AttachedFilter(BaseModel):
    key: str
    name: str
    filterType: TestFilterType
    content: str


class TestStructureTreeNodeInformation(BaseModel):
    key: str
    numbering: str
    parentKey: str
    name: str
    uniqueID: str
    orderPos: int
    matchesFilter: bool


class TestStructureTreeNode(BaseModel):
    elementType: TestStructureElementType
    base: TestStructureTreeNodeInformation
    spec: Optional[TestStructureSpecification]
    aut: Optional[TestStructureAutomation]
    exec: Optional[TestStructureExecution]
    filters: List[AttachedFilter]


class TestStructureTree(BaseModel):
    root: Optional[TestStructureTreeNode]
    nodes: List[TestStructureTreeNode]


class AllModels(BaseModel):
    ProjectMember: ProjectMember
    ProjectDetails: ProjectDetails
    TOVDetails: TOVDetails
    CycleDetails: CycleDetails
    UserDetails: UserDetails
    TestStructureTree: TestStructureTree
    TestCaseDetails: TestCaseDetails
    InteractionDetails: InteractionDetails
    InteractionSpecificationSummary: InteractionSpecificationSummary
    InteractionExecutionSummary: InteractionExecutionSummary
    ParameterSummary: ParameterSummary
    TestCaseSpecificationDetails: TestCaseSpecificationDetails
    TestCaseExecutionDetails: TestCaseExecutionDetails
    TestStructureSpecification: TestStructureSpecification
    TestStructureAutomation: TestStructureAutomation
    TestStructureExecution: TestStructureExecution
    AttachedFilter: AttachedFilter
    TestStructureTreeNodeInformation: TestStructureTreeNodeInformation
    TestStructureTreeNode: TestStructureTreeNode
    TestCaseExecutionSummary: TestCaseExecutionSummary
    TestCaseSetExecutionSummary: TestCaseSetExecutionSummary
    ActivityStatus: ActivityStatus
    ExecStatus: ExecStatus
    VerdictStatus: VerdictStatus
    SpecStatus: SpecStatus
    DataTypeSummary: DataTypeSummary
    TestCaseSetDetails: TestCaseSetDetails
    TestCaseSetSpecificationSummary: TestCaseSetSpecificationSummary
    TestCaseSpecificationSummary: TestCaseSpecificationSummary
    TestCaseSummary: TestCaseSummary




