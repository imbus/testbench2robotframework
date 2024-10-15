# generated by datamodel-codegen:
#   filename:  model.yml
#   timestamp: 2023-09-25T09:28:04+00:00

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ActivityStatus(BaseModel):
    enum: List[str]
    title: str
    type: str


class Content(BaseModel):
    title: str
    type: str


class FilterType(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class Key(BaseModel):
    title: str
    type: str


class Name(BaseModel):
    title: str
    type: str


class Properties(BaseModel):
    content: Content
    filterType: FilterType
    key: Key
    name: Name


class AttachedFilter(BaseModel):
    properties: Properties
    required: List[str]
    title: str
    type: str


class CallType(BaseModel):
    enum: List[str]
    title: str
    type: str


class Description(BaseModel):
    title: str
    type: str


class UniqueId(BaseModel):
    title: str
    type: str


class AnyOfItem(BaseModel):
    type: str


class Version(BaseModel):
    anyOf: List[AnyOfItem]
    default: None
    title: str


class Properties1(BaseModel):
    description: Description
    key: Key
    name: Name
    uniqueId: UniqueId
    version: Version


class ConditionSummary(BaseModel):
    properties: Properties1
    required: List[str]
    title: str
    type: str


class DataTypeKind(BaseModel):
    enum: List[str]
    title: str
    type: str


class Kind(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class Path(BaseModel):
    title: str
    type: str


class UniqueID(BaseModel):
    title: str
    type: str


class Version1(BaseModel):
    anyOf: List[AnyOfItem]
    title: str


class Properties2(BaseModel):
    key: Key
    kind: Kind
    name: Name
    path: Path
    uniqueID: UniqueID
    version: Version1


class DataTypeSummary(BaseModel):
    properties: Properties2
    required: List[str]
    title: str
    type: str


class ExecutionStatus(BaseModel):
    enum: List[str]
    title: str
    type: str


class ExecutionVerdict(BaseModel):
    enum: List[str]
    title: str
    type: str


class FilterType1(BaseModel):
    enum: List[str]
    title: str
    type: str


class AnyOfItem2(BaseModel):
    field_ref: Optional[str] = Field(None, alias='$ref')
    type: Optional[str] = None


class Exec(BaseModel):
    anyOf: List[AnyOfItem2]


class InteractionType(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class Items(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class Interactions(BaseModel):
    items: Items
    title: str
    type: str


class Parameters(BaseModel):
    items: Items
    title: str
    type: str


class Spec(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class AnyOfItem3(BaseModel):
    type: str


class Version2(BaseModel):
    anyOf: List[AnyOfItem3]
    title: str


class Properties3(BaseModel):
    exec: Exec
    interactionType: InteractionType
    interactions: Interactions
    key: Key
    name: Name
    parameters: Parameters
    path: Path
    spec: Spec
    uniqueID: UniqueID
    version: Version2


class InteractionDetails(BaseModel):
    properties: Properties3
    required: List[str]
    title: str
    type: str


class Comments(BaseModel):
    title: str
    type: str


class CurrentUser(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class Duration(BaseModel):
    title: str
    type: str


class References(BaseModel):
    items: Items
    title: str
    type: str


class Tester(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class Time(BaseModel):
    title: str
    type: str


class Verdict(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class Properties4(BaseModel):
    comments: Comments
    currentUser: CurrentUser
    duration: Duration
    references: References
    tester: Tester
    time: Time
    verdict: Verdict


class InteractionExecutionSummary(BaseModel):
    properties: Properties4
    required: List[str]
    title: str
    type: str


class CallId(BaseModel):
    title: str
    type: str


class CallType1(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class PostConditions(BaseModel):
    items: Items
    title: str
    type: str


class PreConditions(BaseModel):
    items: Items
    title: str
    type: str


class References1(BaseModel):
    items: Items
    title: str
    type: str


class SequencePhase(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class Properties5(BaseModel):
    callId: CallId
    callType: CallType1
    comments: Comments
    description: Description
    postConditions: PostConditions
    preConditions: PreConditions
    references: References1
    sequencePhase: SequencePhase


class InteractionSpecificationSummary(BaseModel):
    properties: Properties5
    required: List[str]
    title: str
    type: str


class InteractionType1(BaseModel):
    enum: List[str]
    title: str
    type: str


class InteractionVerdict(BaseModel):
    enum: List[str]
    title: str
    type: str


class IsVariantsMarker(BaseModel):
    title: str
    type: str


class Properties6(BaseModel):
    isVariantsMarker: IsVariantsMarker
    key: Key
    name: Name


class Keyword(BaseModel):
    properties: Properties6
    required: List[str]
    title: str
    type: str


class ParameterDefinitionType(BaseModel):
    enum: List[str]
    title: str
    type: str


class DataType(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class DefinitionType(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class UseType(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class Value(BaseModel):
    anyOf: List[AnyOfItem3]
    title: str


class ValueType(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class Properties7(BaseModel):
    dataType: DataType
    definitionType: DefinitionType
    key: Key
    name: Name
    useType: UseType
    value: Value
    valueType: ValueType


class ParameterSummary(BaseModel):
    properties: Properties7
    required: List[str]
    title: str
    type: str


class ParameterUseType(BaseModel):
    enum: List[str]
    title: str
    type: str


class ParameterValueType(BaseModel):
    enum: List[str]
    title: str
    type: str


class Priority(BaseModel):
    enum: List[str]
    title: str
    type: str


class Type(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class Properties8(BaseModel):
    path: Path
    type: Type


class Reference(BaseModel):
    properties: Properties8
    required: List[str]
    title: str
    type: str


class ReferenceType(BaseModel):
    enum: List[str]
    title: str
    type: str


class Edited(BaseModel):
    title: str
    type: str


class Properties9(BaseModel):
    edited: Edited
    key: Key


class RequirementReference(BaseModel):
    properties: Properties9
    required: List[str]
    title: str
    type: str


class SequencePhase1(BaseModel):
    enum: List[str]
    title: str
    type: str


class SpecificationStatus(BaseModel):
    enum: List[str]
    title: str
    type: str


class AnyOfItem5(BaseModel):
    field_ref: Optional[str] = Field(None, alias='$ref')
    type: Optional[str] = None


class Exec1(BaseModel):
    anyOf: List[AnyOfItem5]


class Interactions1(BaseModel):
    items: Items
    title: str
    type: str


class Parameters1(BaseModel):
    items: Items
    title: str
    type: str


class Properties10(BaseModel):
    exec: Exec1
    interactions: Interactions1
    parameters: Parameters1
    spec: Spec
    uniqueID: UniqueID


class TestCaseDetails(BaseModel):
    properties: Properties10
    required: List[str]
    title: str
    type: str


class ActualDuration(BaseModel):
    title: str
    type: str


class Items8(BaseModel):
    type: str


class Defects(BaseModel):
    items: Items8
    title: str
    type: str


class ExecStatus(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class Items9(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class Keywords(BaseModel):
    items: Items9
    title: str
    type: str


class PlannedDuration(BaseModel):
    title: str
    type: str


class References2(BaseModel):
    items: Items9
    title: str
    type: str


class Status(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class Tester1(BaseModel):
    anyOf: List[AnyOfItem5]


class Udfs(BaseModel):
    items: Items9
    title: str
    type: str


class AnyOfItem7(BaseModel):
    type: str


class Version3(BaseModel):
    anyOf: List[AnyOfItem7]
    title: str


class Properties11(BaseModel):
    actualDuration: ActualDuration
    comments: Comments
    currentUser: CurrentUser
    defects: Defects
    execStatus: ExecStatus
    key: Key
    keywords: Keywords
    plannedDuration: PlannedDuration
    references: References2
    status: Status
    tester: Tester1
    udfs: Udfs
    verdict: Verdict
    version: Version3


class TestCaseExecutionDetails(BaseModel):
    properties: Properties11
    required: List[str]
    title: str
    type: str


class Comments3(BaseModel):
    default: str
    title: str
    type: str


class Items12(BaseModel):
    type: str


class AnyOfItem8(BaseModel):
    items: Optional[Items12] = None
    type: str


class Defects1(BaseModel):
    anyOf: List[AnyOfItem8]
    default: None
    title: str


class AllOfItem(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class ExecStatus1(BaseModel):
    allOf: List[AllOfItem]
    default: str


class Status1(BaseModel):
    allOf: List[AllOfItem]
    default: str


class AnyOfItem9(BaseModel):
    field_ref: Optional[str] = Field(None, alias='$ref')
    type: Optional[str] = None


class Tester2(BaseModel):
    anyOf: List[AnyOfItem9]
    default: None


class Verdict2(BaseModel):
    allOf: List[AllOfItem]
    default: str


class Properties12(BaseModel):
    comments: Comments3
    defects: Defects1
    execStatus: ExecStatus1
    key: Key
    status: Status1
    tester: Tester2
    verdict: Verdict2


class TestCaseExecutionSummary(BaseModel):
    properties: Properties12
    required: List[str]
    title: str
    type: str


class Exec2(BaseModel):
    anyOf: List[AnyOfItem9]


class Numbering(BaseModel):
    title: str
    type: str


class Items13(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class TestCases(BaseModel):
    items: Items13
    title: str
    type: str


class Properties13(BaseModel):
    exec: Exec2
    key: Key
    name: Name
    numbering: Numbering
    spec: Spec
    testCases: TestCases
    uniqueID: UniqueID


class TestCaseSetDetails(BaseModel):
    properties: Properties13
    required: List[str]
    title: str
    type: str


class Comments4(BaseModel):
    title: str
    type: str


class Keywords1(BaseModel):
    items: Items13
    title: str
    type: str


class Udfs1(BaseModel):
    items: Items13
    title: str
    type: str


class Properties14(BaseModel):
    comments: Comments4
    key: Key
    keywords: Keywords1
    udfs: Udfs1


class TestCaseSetExecutionSummary(BaseModel):
    properties: Properties14
    required: List[str]
    title: str
    type: str


class AnyOfItem11(BaseModel):
    type: str


class DueDate(BaseModel):
    anyOf: List[AnyOfItem11]
    title: str


class Keywords2(BaseModel):
    items: Items13
    title: str
    type: str


class PostConditions1(BaseModel):
    items: Items13
    title: str
    type: str


class PreConditions1(BaseModel):
    items: Items13
    title: str
    type: str


class AnyOfItem12(BaseModel):
    field_ref: Optional[str] = Field(None, alias='$ref')
    type: Optional[str] = None


class Priority1(BaseModel):
    anyOf: List[AnyOfItem12]


class References3(BaseModel):
    items: Items13
    title: str
    type: str


class Requirements(BaseModel):
    items: Items13
    title: str
    type: str


class Responsible(BaseModel):
    anyOf: List[AnyOfItem12]


class ReviewComment(BaseModel):
    title: str
    type: str


class Reviewer(BaseModel):
    anyOf: List[AnyOfItem12]


class Status2(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class Udfs2(BaseModel):
    items: Items13
    title: str
    type: str


class Properties15(BaseModel):
    description: Description
    dueDate: DueDate
    key: Key
    keywords: Keywords2
    postConditions: PostConditions1
    preConditions: PreConditions1
    priority: Priority1
    references: References3
    requirements: Requirements
    responsible: Responsible
    reviewComment: ReviewComment
    reviewer: Reviewer
    status: Status2
    udfs: Udfs2


class TestCaseSetSpecificationSummary(BaseModel):
    properties: Properties15
    required: List[str]
    title: str
    type: str


class Keywords3(BaseModel):
    items: Items13
    title: str
    type: str


class Requirements1(BaseModel):
    items: Items13
    title: str
    type: str


class Udfs3(BaseModel):
    items: Items13
    title: str
    type: str


class Properties16(BaseModel):
    comments: Comments4
    key: Key
    keywords: Keywords3
    requirements: Requirements1
    udfs: Udfs3


class TestCaseSpecificationDetails(BaseModel):
    properties: Properties16
    required: List[str]
    title: str
    type: str


class Requirements2(BaseModel):
    items: Items13
    title: str
    type: str


class Properties17(BaseModel):
    comments: Comments4
    key: Key
    requirements: Requirements2


class TestCaseSpecificationSummary(BaseModel):
    properties: Properties17
    required: List[str]
    title: str
    type: str


class Exec3(BaseModel):
    anyOf: List[AnyOfItem12]
    default: None


class Index(BaseModel):
    title: str
    type: str


class Properties18(BaseModel):
    exec: Exec3
    index: Index
    spec: Spec
    uniqueID: UniqueID


class TestCaseSummary(BaseModel):
    properties: Properties18
    required: List[str]
    title: str
    type: str


class Locker(BaseModel):
    anyOf: List[AnyOfItem12]


class Properties19(BaseModel):
    key: Key
    locker: Locker
    status: Status2


class TestStructureAutomation(BaseModel):
    properties: Properties19
    required: List[str]
    title: str
    type: str


class ExecStatus2(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class Locker1(BaseModel):
    anyOf: List[AnyOfItem12]


class Verdict3(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class Properties20(BaseModel):
    execStatus: ExecStatus2
    key: Key
    locker: Locker1
    status: Status2
    verdict: Verdict3


class TestStructureExecution(BaseModel):
    properties: Properties20
    required: List[str]
    title: str
    type: str


class Locker2(BaseModel):
    anyOf: List[AnyOfItem12]


class Properties21(BaseModel):
    key: Key
    locker: Locker2
    status: Status2


class TestStructureSpecification(BaseModel):
    properties: Properties21
    required: List[str]
    title: str
    type: str


class Nodes(BaseModel):
    items: Items13
    title: str
    type: str


class Root(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class Properties22(BaseModel):
    nodes: Nodes
    root: Root


class TestStructureTree(BaseModel):
    properties: Properties22
    required: List[str]
    title: str
    type: str


class Automation(BaseModel):
    anyOf: List[AnyOfItem12]


class BaseInformation(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class ElementType(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class Execution(BaseModel):
    anyOf: List[AnyOfItem12]


class Filters(BaseModel):
    items: Items13
    title: str
    type: str


class Specification(BaseModel):
    anyOf: List[AnyOfItem12]


class Properties23(BaseModel):
    automation: Automation
    baseInformation: BaseInformation
    elementType: ElementType
    execution: Execution
    filters: Filters
    specification: Specification


class TestStructureTreeNode(BaseModel):
    properties: Properties23
    required: List[str]
    title: str
    type: str


class MatchesFilter(BaseModel):
    title: str
    type: str


class OrderPos(BaseModel):
    title: str
    type: str


class ParentKey(BaseModel):
    title: str
    type: str


class Properties24(BaseModel):
    key: Key
    matchesFilter: MatchesFilter
    name: Name
    numbering: Numbering
    orderPos: OrderPos
    parentKey: ParentKey
    uniqueID: UniqueID


class TestStructureTreeNodeInformation(BaseModel):
    properties: Properties24
    required: List[str]
    title: str
    type: str


class TestStructureTreeNodeType(BaseModel):
    enum: List[str]
    title: str
    type: str


class UdfType(BaseModel):
    enum: List[str]
    title: str
    type: str


class Value1(BaseModel):
    title: str
    type: str


class Properties25(BaseModel):
    key: Key
    name: Name
    value: Value1
    valueType: ValueType


class UserDefinedField(BaseModel):
    properties: Properties25
    required: List[str]
    title: str
    type: str


class Properties26(BaseModel):
    key: Key
    name: Name


class UserReference(BaseModel):
    properties: Properties26
    required: List[str]
    title: str
    type: str


class FieldDefs(BaseModel):
    ActivityStatus: ActivityStatus
    AttachedFilter: AttachedFilter
    CallType: CallType
    ConditionSummary: ConditionSummary
    DataTypeKind: DataTypeKind
    DataTypeSummary: DataTypeSummary
    ExecutionStatus: ExecutionStatus
    ExecutionVerdict: ExecutionVerdict
    FilterType: FilterType1
    InteractionDetails: InteractionDetails
    InteractionExecutionSummary: InteractionExecutionSummary
    InteractionSpecificationSummary: InteractionSpecificationSummary
    InteractionType: InteractionType1
    InteractionVerdict: InteractionVerdict
    Keyword: Keyword
    ParameterDefinitionType: ParameterDefinitionType
    ParameterSummary: ParameterSummary
    ParameterUseType: ParameterUseType
    ParameterValueType: ParameterValueType
    Priority: Priority
    Reference: Reference
    ReferenceType: ReferenceType
    RequirementReference: RequirementReference
    SequencePhase: SequencePhase1
    SpecificationStatus: SpecificationStatus
    TestCaseDetails: TestCaseDetails
    TestCaseExecutionDetails: TestCaseExecutionDetails
    TestCaseExecutionSummary: TestCaseExecutionSummary
    TestCaseSetDetails: TestCaseSetDetails
    TestCaseSetExecutionSummary: TestCaseSetExecutionSummary
    TestCaseSetSpecificationSummary: TestCaseSetSpecificationSummary
    TestCaseSpecificationDetails: TestCaseSpecificationDetails
    TestCaseSpecificationSummary: TestCaseSpecificationSummary
    TestCaseSummary: TestCaseSummary
    TestStructureAutomation: TestStructureAutomation
    TestStructureExecution: TestStructureExecution
    TestStructureSpecification: TestStructureSpecification
    TestStructureTree: TestStructureTree
    TestStructureTreeNode: TestStructureTreeNode
    TestStructureTreeNodeInformation: TestStructureTreeNodeInformation
    TestStructureTreeNodeType: TestStructureTreeNodeType
    UdfType: UdfType
    UserDefinedField: UserDefinedField
    UserReference: UserReference


class TestCaseDetails1(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class TestCaseSetDetails1(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class TestStructureTree1(BaseModel):
    field_ref: str = Field(..., alias='$ref')


class Properties27(BaseModel):
    TestCaseDetails: TestCaseDetails1
    TestCaseSetDetails: TestCaseSetDetails1
    TestStructureTree: TestStructureTree1


class Model(BaseModel):
    field_defs: FieldDefs = Field(..., alias='$defs')
    properties: Properties27
    required: List[str]
    title: str
    type: str
