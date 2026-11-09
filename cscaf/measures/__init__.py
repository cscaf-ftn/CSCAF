"""The measures of the paper (Table 2, Equations (1) to (8)) and the analyses built on them.

- `Bands`: the weighting of a best-match similarity (Section 3.4);
- `RoleMapping`: the 227 role-statement rows of the ECSF (Section 3.1);
- `CurriculumCoverage`: C_P(s) and C_P(r), Equations (2) and (3);
- `AdvertisementDemand`: B_A(s), B_A(r) and L_A(r), Equations (4) to (6);
- `DemandWeightedGap`: G_P,A(r), Equation (7);
- `Recommender`, `CourseAddition`: the recommended statements and the course addition (Section 4.2);
- `KnownGroups`: the known-groups validity of Section 4.1.
"""
from cscaf.measures.advertisement_demand import AdvertisementDemand
from cscaf.measures.bands import Bands
from cscaf.measures.course_addition import CourseAddition
from cscaf.measures.coverage_change import CoverageChange
from cscaf.measures.curriculum_coverage import CurriculumCoverage
from cscaf.measures.demand_weighted_gap import DemandWeightedGap
from cscaf.measures.known_groups import KnownGroups
from cscaf.measures.recommendation import Recommendation
from cscaf.measures.recommended_statement import RecommendedStatement
from cscaf.measures.recommender import Recommender
from cscaf.measures.role_mapping import RoleMapping

__all__ = ["AdvertisementDemand", "Bands", "CourseAddition", "CoverageChange", "CurriculumCoverage",
           "DemandWeightedGap", "KnownGroups", "Recommendation", "RecommendedStatement", "Recommender",
           "RoleMapping"]
