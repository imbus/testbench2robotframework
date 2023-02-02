# pylint: skip-file
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from optparse import Option
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


class FilterType(StrEnum):
    TestThemeFilter = "TestThemeFilter"
    TestCaseSetFilter = "TestCaseSetFilter"
    TestCaseFilter = "TestCaseFilter"


class TestStructureTreeNodeType(StrEnum):
    Root = "Root"
    TestTheme = "TestTheme"
    TestCaseSet = "TestCaseSet"


class Priority(StrEnum):
    High = "High"
    Medium = "Medium"
    Low = "Low"


class ReferenceType(StrEnum):
    Reference = "Reference"
    Hyperlink = "Hyperlink"
    Attachment = "Attachment"


class SpecificationStatus(StrEnum):
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


class ExecutionVerdict(StrEnum):
    Undefined = "Undefined"
    Pass = "Pass"
    Fail = "Fail"
    ToVerify = "ToVerify"


class ActivityStatus(StrEnum):
    NotPlanned = "NotPlanned"
    Planned = "Planned"
    Assigned = "Assigned"
    Running = "Running"
    Canceled = "Canceled"
    Skipped = "Skipped"
    Performed = "Performed"


class ExecutionStatus(StrEnum):
    NotBlocked = "NotBlocked"
    Blocked = "Blocked"


class UdfType(StrEnum):
    String = "String"
    Enumeration = "Enumeration"
    Boolean = "Boolean"


class SequencePhase(StrEnum):
    Setup = "Setup"
    TestStep = "TestStep"
    Teardown = "Teardown"


class CallType(StrEnum):
    Check = "Check"
    Flow = "Flow"


class InteractionType(StrEnum):
    Compound = "Compound"
    Atomic = "Atomic"
    Textuell = "Textuell"


class ParameterType(StrEnum):
    DetailedInstance = "DetailedInstance"
    Unknown = "Unknown"
    InstanceTable = "InstanceTable"
    AtomicInstance = "AtomicInstance"


class ParameterUseType(StrEnum):
    CallByReference = "CallByReference"
    CallByValue = "CallByValue"
    CallByReferenceMandatory = "CallByReferenceMandatory"


@dataclass
class ProjectMember:
    userkey: str
    userLogin: str
    userName: str
    projectkey: str
    projectName: str
    roles: List[str]


@dataclass
class ProjectDetails:
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


@dataclass
class TOVDetails:
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


@dataclass
class CycleDetails:
    key: str
    creationTime: str
    name: str
    status: str
    visibility: bool
    description: str
    startDate: Optional[str] = None
    endDate: Optional[str] = None


@dataclass
class UserDetails:
    key: str
    login: str
    name: str
    email: str
    passwordExpired: bool
    active: bool


@dataclass
class UserSummary:
    key: str
    login: str
    name: str
    active: bool

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            key=dictionary.get("key", ""),
            login=dictionary.get("login", ""),
            name=dictionary.get("name", ""),
            active=dictionary.get("active", True),
        )


@dataclass
class UserDefinedField:
    key: str
    name: str
    value: str
    valueType: UdfType

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            key=dictionary.get("key", ""),
            name=dictionary.get("name", ""),
            value=dictionary.get("value", ""),
            valueType=UdfType(dictionary.get("valueType", UdfType.String)),
        )

    @property
    def robot_tag(self) -> Optional[str]:
        if self.valueType == UdfType.Enumeration:
            return f"{self.name}:{self.value}"
        elif self.valueType == UdfType.String and self.value:
            return f"{self.name}:{self.value}"
        elif self.valueType == UdfType.Boolean and self.value == "true":
            return self.name
        return None


@dataclass
class Keyword:
    key: str
    name: str
    isVariantsMarker: bool

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            key=dictionary.get("key", ""),
            name=dictionary.get("name", ""),
            isVariantsMarker=dictionary.get("isVariantsMarker", False),
        )


@dataclass
class Reference:
    type: ReferenceType
    path: str

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            type=ReferenceType(dictionary.get("type", ReferenceType.Reference)),
            path=dictionary.get("path", ""),
        )


@dataclass
class UserReference:
    key: str
    name: str

    @classmethod
    def from_dict(cls, dictionary):
        return cls(key=dictionary.get("key", ""), name=dictionary.get("name", ""))


@dataclass
class RequirementReference:
    key: str
    edited: bool

    @classmethod
    def from_dict(cls, dictionary):
        return cls(key=dictionary.get("key", ""), edited=dictionary.get("edited", False))


@dataclass
class ConditionSummary:
    key: str
    uniqueId: str
    name: str
    description: str
    version: Optional[str] = None

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            key=dictionary.get("key", ""),
            uniqueId=dictionary.get("uniqueId", ""),
            name=dictionary.get("name", ""),
            description=dictionary.get("description", ""),
            version=dictionary.get("version", None),
        )


@dataclass
class TestCaseSetSpecificationSummary:
    key: str
    description: str
    reviewComment: str
    status: SpecificationStatus
    priority: Optional[Priority]
    responsible: Optional[UserReference]
    dueDate: Optional[str]
    reviewer: Optional[UserReference]
    udfs: List[UserDefinedField]
    keywords: List[Keyword]
    references: List[Reference]
    requirements: List[RequirementReference]
    preConditions: List[ConditionSummary]
    postConditions: List[ConditionSummary]

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            key=dictionary.get("key", ""),
            description=dictionary.get("description", ""),
            reviewComment=dictionary.get("reviewComment", ""),
            status=SpecificationStatus(dictionary.get("status", SpecificationStatus.Planned)),
            priority=Priority(dictionary.get("priority")) if dictionary.get("priority") else None,
            responsible=UserReference.from_dict(dictionary.get("responsible", {}))
            if dictionary.get("responsible")
            else None,
            dueDate=dictionary.get("dueDate", None),
            reviewer=UserReference.from_dict(dictionary.get("reviewer", {}))
            if dictionary.get("reviewer")
            else None,
            udfs=[UserDefinedField.from_dict(udf) for udf in dictionary.get("udfs", [])],
            keywords=[Keyword.from_dict(keyword) for keyword in dictionary.get("keywords", [])],
            references=dictionary.get("references", ""),
            requirements=[
                RequirementReference.from_dict(requirement)
                for requirement in dictionary.get("requirements", [])
            ],
            preConditions=[
                ConditionSummary.from_dict(condition)
                for condition in dictionary.get("preConditions", [])
            ],
            postConditions=[
                ConditionSummary.from_dict(condition)
                for condition in dictionary.get("postConditions", [])
            ],
        )


@dataclass
class TestCaseSpecificationDetails:
    key: str
    comments: str
    udfs: List[UserDefinedField]
    keywords: List[Keyword]
    requirements: List[RequirementReference]

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            key=dictionary.get("key", ""),
            comments=dictionary.get("comments", ""),
            udfs=[UserDefinedField.from_dict(udf) for udf in dictionary.get("udfs", [])],
            keywords=[Keyword.from_dict(keyword) for keyword in dictionary.get("keywords", [])],
            requirements=[
                RequirementReference.from_dict(requirement)
                for requirement in dictionary.get("requirements", [])
            ],
        )


@dataclass
class TestCaseSetExecutionSummary:
    key: str
    comments: str
    udfs: List[UserDefinedField]
    keywords: List[Keyword]

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            key=dictionary.get("key", ""),
            comments=dictionary.get("comments", ""),
            udfs=[UserDefinedField.from_dict(udf) for udf in dictionary.get("udfs", [])],
            keywords=[Keyword.from_dict(keyword) for keyword in dictionary.get("keywords", [])],
        )


@dataclass
class TestCaseSpecificationSummary:
    key: str
    comments: str
    requirements: List[RequirementReference]

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            key=dictionary.get("key", ""),
            comments=dictionary.get("comments", ""),
            requirements=[
                RequirementReference.from_dict(requirement)
                for requirement in dictionary.get("requirements", [])
            ],
        )


@dataclass
class TestCaseExecutionSummary:
    key: str
    comments: str = ""
    status: ActivityStatus = ActivityStatus.Planned
    execStatus: ExecutionStatus = ExecutionStatus.NotBlocked
    verdict: ExecutionVerdict = ExecutionVerdict.Undefined
    defects: Optional[List[int]] = None
    tester: Optional[UserReference] = None

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            key=dictionary.get("key", ""),
            status=ActivityStatus(dictionary.get("status", ActivityStatus.Planned)),
            execStatus=ExecutionStatus(dictionary.get("execStatus", ExecutionStatus.NotBlocked)),
            verdict=ExecutionVerdict(dictionary.get("verdict", ExecutionVerdict.Undefined)),
            comments=dictionary.get("comments", ""),
            defects=dictionary.get("defects", []),
            tester=UserReference.from_dict(dictionary.get("tester"))
            if dictionary.get("tester")
            else None,
        )


@dataclass
class TestCaseSummary:
    uniqueID: str
    index: int
    spec: TestCaseSpecificationSummary
    exec: Optional[TestCaseExecutionSummary] = None

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            uniqueID=dictionary.get("uniqueID", ""),
            index=dictionary.get("index", 0),
            spec=TestCaseSpecificationSummary.from_dict(dictionary.get("spec", {})),
            exec=TestCaseExecutionSummary.from_dict(dictionary.get("exec"))
            if dictionary.get("exec")
            else None,
        )


@dataclass
class TestCaseExecutionDetails:
    key: str
    status: ActivityStatus
    execStatus: ExecutionStatus
    verdict: ExecutionVerdict
    plannedDuration: int
    actualDuration: int
    currentUser: UserReference
    tester: Optional[UserReference]
    comments: str  # TODO: Insert htmlComment
    version: Optional[str]
    defects: List[int]
    udfs: List[UserDefinedField]
    keywords: List[Keyword]
    references: List[Reference]

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            key=dictionary.get("key", ""),
            status=ActivityStatus(dictionary.get("status", ActivityStatus.Planned)),
            execStatus=ExecutionStatus(dictionary.get("execStatus", ExecutionStatus.NotBlocked)),
            verdict=ExecutionVerdict(dictionary.get("verdict", ExecutionVerdict.Undefined)),
            plannedDuration=dictionary.get("plannedDuration", 0),
            actualDuration=dictionary.get("actualDuration", 0),
            currentUser=UserReference.from_dict(dictionary.get("currentUser", {})),
            tester=UserReference.from_dict(dictionary.get("tester", {}))
            if dictionary.get("tester")
            else None,
            comments=dictionary.get("comments", ""),
            version=dictionary.get("version", None),
            defects=dictionary.get("defects", []),
            udfs=[UserDefinedField.from_dict(udf) for udf in dictionary.get("udfs", [])],
            keywords=[Keyword.from_dict(keyword) for keyword in dictionary.get("keywords", [])],
            references=dictionary.get("references", []),
        )


@dataclass
class TestCaseSetDetails:
    key: str
    numbering: str
    uniqueID: str
    name: str
    spec: TestCaseSetSpecificationSummary
    exec: Optional[TestCaseSetExecutionSummary]
    testCases: List[TestCaseSummary]

    @classmethod
    def from_dict(cls, dictionary) -> TestCaseSetDetails:
        return cls(
            key=dictionary.get("key", ""),
            numbering=dictionary.get("numbering", ""),
            uniqueID=dictionary.get("uniqueID", ""),
            name=dictionary.get("name", ""),
            spec=TestCaseSetSpecificationSummary.from_dict(dictionary.get("spec", {})),
            exec=TestCaseSetExecutionSummary.from_dict(dictionary.get("exec", {}))
            if dictionary.get("exec")
            else None,
            testCases=[
                TestCaseSummary.from_dict(test_case)
                for test_case in dictionary.get("testCases", [])
            ],
        )


@dataclass
class InteractionExecutionSummary:
    verdict: InteractionVerdict
    time: str
    duration: int
    currentUser: UserReference
    tester: UserReference
    comments: str
    references: List[Reference]

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            verdict=InteractionVerdict(dictionary.get("verdict", InteractionVerdict.Undefined)),
            time=dictionary.get("time", ""),
            duration=dictionary.get("duration", 0),
            currentUser=UserReference.from_dict(dictionary.get("currentUser", {})),
            tester=UserReference.from_dict(dictionary.get("tester", {})),
            comments=dictionary.get("comments", ""),
            references=dictionary.get("references", []),
        )


@dataclass
class InteractionSpecificationSummary:
    callId: int
    sequencePhase: SequencePhase
    callType: CallType
    description: str
    comments: str
    references: List[Reference]
    preConditions: List[ConditionSummary]
    postConditions: List[ConditionSummary]

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            callId=dictionary.get("callId", ""),
            sequencePhase=SequencePhase(dictionary.get("sequencePhase", SequencePhase.TestStep)),
            callType=CallType(dictionary.get("callType", CallType.Flow)),
            description=dictionary.get("description", ""),
            comments=dictionary.get("comments", ""),
            references=dictionary.get("references", ""),
            preConditions=[
                ConditionSummary.from_dict(condition)
                for condition in dictionary.get("preConditions", [])
            ],
            postConditions=[
                ConditionSummary.from_dict(condition)
                for condition in dictionary.get("postConditions", [])
            ],
        )


@dataclass
class ParameterSummary:
    name: str
    value: str
    version: Optional[str]
    parameterType: ParameterType
    parameterUseType: ParameterUseType
    dataTypeName: str
    dataTypePath: str
    dataTypeUniqueID: str

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            name=dictionary.get("name", ""),
            value=dictionary.get("value", ""),
            version=dictionary.get(
                "version",
            ),
            parameterType=ParameterType(
                dictionary.get("parameterType", ParameterType.AtomicInstance)
            ),
            parameterUseType=ParameterUseType(
                dictionary.get("parameterUseType", ParameterUseType.CallByValue)
            ),
            dataTypeName=dictionary.get("dataTypeName", ""),
            dataTypePath=dictionary.get("dataTypePath", ""),
            dataTypeUniqueID=dictionary.get("dataTypeUniqueID", ""),
        )


@dataclass
class InteractionDetails:
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

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            key=dictionary.get("key", ""),
            uniqueID=dictionary.get("uniqueID", ""),
            name=dictionary.get("name", ""),
            version=dictionary.get("version", ""),
            interactionType=InteractionType(
                dictionary.get("interactionType", InteractionType.Atomic)
            ),
            path=dictionary.get("path", ""),
            spec=InteractionSpecificationSummary.from_dict(dictionary.get("spec")),
            exec=InteractionExecutionSummary.from_dict(dictionary.get("exec"))
            if dictionary.get("exec")
            else None,
            parameters=[
                ParameterSummary.from_dict(param) for param in dictionary.get("parameters", [])
            ],
            interactions=[
                InteractionDetails.from_dict(interaction)
                for interaction in dictionary.get("interactions", [])
            ],
        )


@dataclass
class TestCaseDetails:
    uniqueID: str
    spec: TestCaseSpecificationDetails
    exec: Optional[TestCaseExecutionDetails]
    interactions: List[InteractionDetails]
    parameters: List[ParameterSummary]

    @classmethod
    def from_dict(cls, dictionary) -> TestCaseDetails:
        return cls(
            uniqueID=dictionary.get("uniqueID"),
            spec=TestCaseSpecificationDetails.from_dict(dictionary.get("spec")),
            exec=TestCaseExecutionDetails.from_dict(dictionary.get("exec"))
            if dictionary.get("exec")
            else None,
            interactions=[
                InteractionDetails.from_dict(interaction)
                for interaction in dictionary.get("interactions", [])
            ],
            parameters=[
                ParameterSummary.from_dict(parameter)
                for parameter in dictionary.get("parameters", [])
            ],
        )


@dataclass
class TestStructureSpecification:
    key: str
    locker: Optional[UserReference]
    status: SpecificationStatus

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            key=dictionary.get("key", "-1"),
            locker=UserReference.from_dict(dictionary.get("locker", {}))
            if dictionary.get("locker")
            else None,
            status=SpecificationStatus(dictionary.get("status", SpecificationStatus.Planned)),
        )


@dataclass
class TestStructureAutomation:
    key: str
    locker: Optional[UserReference]
    status: SpecificationStatus

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            key=dictionary.get("key", "-1"),
            locker=UserReference.from_dict(dictionary.get("locker", {}))
            if dictionary.get("locker")
            else None,
            status=SpecificationStatus(dictionary.get("status", SpecificationStatus.Planned)),
        )


@dataclass
class TestStructureExecution:
    key: str
    locker: Optional[UserReference]
    status: ActivityStatus
    execStatus: ExecutionStatus
    verdict: ExecutionVerdict

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            key=dictionary.get("key", "-1"),
            locker=UserReference.from_dict(dictionary.get("locker", {}))
            if dictionary.get("locker")
            else None,
            status=ActivityStatus(dictionary.get("status", ActivityStatus.Planned)),
            execStatus=ExecutionStatus(dictionary.get("execStatus", ExecutionStatus.NotBlocked)),
            verdict=ExecutionVerdict(dictionary.get("verdict", ExecutionVerdict.Undefined)),
        )


@dataclass
class AttachedFilter:
    key: str
    name: str
    filterType: FilterType
    content: str

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            key=dictionary.get("key", "-1"),
            name=dictionary.get("name", ""),
            filterType=FilterType(dictionary.get("filterType", FilterType.TestCaseSetFilter)),
            content=dictionary.get("content", ""),
        )


@dataclass
class TestStructureTreeNodeInformation:
    key: str
    numbering: str
    parentKey: str
    name: str
    uniqueID: str
    orderPos: int
    matchesFilter: bool

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            key=dictionary.get("key", "-1"),
            numbering=dictionary.get("numbering", "-1"),
            parentKey=dictionary.get("parentKey", "-1"),
            name=dictionary.get("name", ""),
            uniqueID=dictionary.get("uniqueID", ""),
            orderPos=dictionary.get("orderPos", "-1"),
            matchesFilter=dictionary.get("matchesFilter", True),
        )


@dataclass
class TestStructureTreeNode:
    elementType: TestStructureTreeNodeType
    baseInformation: TestStructureTreeNodeInformation
    specification: Optional[TestStructureSpecification]
    automation: Optional[TestStructureAutomation]
    execution: Optional[TestStructureExecution]
    filters: List[AttachedFilter]

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            elementType=TestStructureTreeNodeType(
                dictionary.get("elementType", TestStructureTreeNodeType.TestTheme)
            ),
            baseInformation=TestStructureTreeNodeInformation.from_dict(
                dictionary.get("baseInformation", {})
            ),
            specification=TestStructureSpecification.from_dict(dictionary.get("specification"))
            if dictionary.get("specification")
            else None,
            automation=TestStructureAutomation.from_dict(dictionary.get("automation"))
            if dictionary.get("automation")
            else None,
            execution=TestStructureExecution.from_dict(dictionary.get("execution"))
            if dictionary.get("execution")
            else None,
            filters=[AttachedFilter.from_dict(filter) for filter in dictionary.get("filters", [])],
        )


@dataclass
class TestStructureTree:
    root: TestStructureTreeNode
    nodes: List[TestStructureTreeNode]

    @classmethod
    def from_dict(cls, dictionary) -> TestStructureTree:
        return cls(
            root=TestStructureTreeNode.from_dict(dictionary.get("root", {}))
            if "root" in dictionary
            else None,
            nodes=[TestStructureTreeNode.from_dict(node) for node in dictionary.get("nodes", [])],
        )
