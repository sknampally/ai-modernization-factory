"""Seed a fictional university enterprise example workspace."""

from __future__ import annotations

from pathlib import Path

_FILES: dict[str, str] = {
    "organizations/organization.yaml": """apiVersion: codestrata.io/v1alpha1
kind: Organization
metadata:
  id: acme
  name: Acme University
spec:
  organizationType: university
  lifecycle: active
""",
    "business-domains/student-services.yaml": """apiVersion: codestrata.io/v1alpha1
kind: BusinessDomain
metadata:
  id: student-services
  name: Student Services
spec:
  owningOrganization: acme
  criticality: high
  lifecycle: strategic
""",
    "business-domains/finance.yaml": """apiVersion: codestrata.io/v1alpha1
kind: BusinessDomain
metadata:
  id: finance
  name: Finance
spec:
  owningOrganization: acme
  criticality: high
  lifecycle: active
""",
    "business-capabilities/student-registration.yaml": """apiVersion: codestrata.io/v1alpha1
kind: BusinessCapability
metadata:
  id: student-registration
  name: Student Registration
spec:
  businessDomain: student-services
  criticality: high
  lifecycle: strategic
""",
    "business-capabilities/financial-aid-processing.yaml": """apiVersion: codestrata.io/v1alpha1
kind: BusinessCapability
metadata:
  id: financial-aid-processing
  name: Financial Aid Processing
spec:
  businessDomain: finance
  criticality: high
  lifecycle: active
""",
    "business-capabilities/admissions.yaml": """apiVersion: codestrata.io/v1alpha1
kind: BusinessCapability
metadata:
  id: admissions
  name: Admissions
spec:
  businessDomain: student-services
  criticality: medium
  lifecycle: active
""",
    "applications/student-information-system.yaml": """apiVersion: codestrata.io/v1alpha1
kind: Application
metadata:
  id: student-information-system
  name: Student Information System
  labels:
    criticality: high
spec:
  applicationType: custom
  lifecycle: strategic
  criticality: high
  businessDomains:
    - student-services
  capabilities:
    - student-registration
    - admissions
  repositories:
    - student-api
    - registration-ui
  services:
    - registration-service
    - identity-service
  owningTeam: student-platform-team
  environments:
    - production
    - test
""",
    "applications/financial-aid-portal.yaml": """apiVersion: codestrata.io/v1alpha1
kind: Application
metadata:
  id: financial-aid-portal
  name: Financial Aid Portal
spec:
  applicationType: custom
  lifecycle: active
  criticality: high
  businessDomains:
    - finance
  capabilities:
    - financial-aid-processing
  repositories:
    - financial-aid-api
  services:
    - financial-aid-service
  owningTeam: finance-apps-team
  environments:
    - production
""",
    "repositories/student-api.yaml": """apiVersion: codestrata.io/v1alpha1
kind: RepositoryReference
metadata:
  id: student-api
  name: Student API
spec:
  provider: github
  canonicalKey: github:acme/student-api
  remoteUrl: https://github.com/acme/student-api
  owningTeam: student-platform-team
  lifecycle: active
  criticality: high
""",
    "repositories/registration-ui.yaml": """apiVersion: codestrata.io/v1alpha1
kind: RepositoryReference
metadata:
  id: registration-ui
  name: Registration UI
spec:
  provider: github
  canonicalKey: github:acme/registration-ui
  remoteUrl: https://github.com/acme/registration-ui
  owningTeam: student-platform-team
  lifecycle: active
""",
    "repositories/financial-aid-api.yaml": """apiVersion: codestrata.io/v1alpha1
kind: RepositoryReference
metadata:
  id: financial-aid-api
  name: Financial Aid API
spec:
  provider: github
  canonicalKey: github:acme/financial-aid-api
  remoteUrl: https://github.com/acme/financial-aid-api
  owningTeam: finance-apps-team
  lifecycle: active
""",
    "services/registration-service.yaml": """apiVersion: codestrata.io/v1alpha1
kind: Service
metadata:
  id: registration-service
  name: Registration Service
spec:
  serviceType: backend
  application: student-information-system
  repositories:
    - student-api
  apis:
    - registration-api
  dataStores:
    - student-oracle
  dependsOn:
    - identity-service
  owningTeam: student-platform-team
  criticality: high
  lifecycle: active
""",
    "services/identity-service.yaml": """apiVersion: codestrata.io/v1alpha1
kind: Service
metadata:
  id: identity-service
  name: Identity Service
spec:
  serviceType: backend
  application: student-information-system
  repositories:
    - student-api
  owningTeam: student-platform-team
  lifecycle: active
""",
    "services/financial-aid-service.yaml": """apiVersion: codestrata.io/v1alpha1
kind: Service
metadata:
  id: financial-aid-service
  name: Financial Aid Service
spec:
  serviceType: backend
  application: financial-aid-portal
  repositories:
    - financial-aid-api
  dataStores:
    - student-oracle
  owningTeam: finance-apps-team
  lifecycle: active
""",
    "apis/registration-api.yaml": """apiVersion: codestrata.io/v1alpha1
kind: API
metadata:
  id: registration-api
  name: Registration API
spec:
  apiType: rest
  protocol: https
  version: v1
  lifecycle: active
  exposure: internal
""",
    "apis/identity-api.yaml": """apiVersion: codestrata.io/v1alpha1
kind: API
metadata:
  id: identity-api
  name: Identity API
spec:
  apiType: rest
  protocol: https
  version: v1
  lifecycle: active
  exposure: internal
""",
    "data-stores/student-oracle.yaml": """apiVersion: codestrata.io/v1alpha1
kind: DataStore
metadata:
  id: student-oracle
  name: Student Oracle
spec:
  type: relational
  technology: oracle
  systemOfRecord: true
  criticality: critical
  lifecycle: active
  dataClassification: confidential
""",
    "data-stores/registration-cache.yaml": """apiVersion: codestrata.io/v1alpha1
kind: DataStore
metadata:
  id: registration-cache
  name: Registration Cache
spec:
  type: cache
  technology: redis
  criticality: medium
  lifecycle: active
""",
    "messaging/student-events.yaml": """apiVersion: codestrata.io/v1alpha1
kind: MessageChannel
metadata:
  id: student-events
  name: Student Events
spec:
  brokerType: kafka
  channelType: topic
  lifecycle: active
""",
    "teams/student-platform-team.yaml": """apiVersion: codestrata.io/v1alpha1
kind: Team
metadata:
  id: student-platform-team
  name: Student Platform Team
spec:
  organization: acme
  lifecycle: active
""",
    "teams/finance-apps-team.yaml": """apiVersion: codestrata.io/v1alpha1
kind: Team
metadata:
  id: finance-apps-team
  name: Finance Apps Team
spec:
  organization: acme
  lifecycle: active
""",
    "environments/production.yaml": """apiVersion: codestrata.io/v1alpha1
kind: Environment
metadata:
  id: production
  name: Production
spec:
  environmentClass: production
  criticality: critical
  lifecycle: active
""",
    "environments/test.yaml": """apiVersion: codestrata.io/v1alpha1
kind: Environment
metadata:
  id: test
  name: Test
spec:
  environmentClass: test
  lifecycle: active
""",
    "standards/spring-standard.yaml": """apiVersion: codestrata.io/v1alpha1
kind: TechnologyStandard
metadata:
  id: spring-standard
  name: Spring Boot Standard
spec:
  status: approved
  approvedTechnology: spring-boot
  guidance: Prefer current supported Spring Boot LTS releases.
""",
    "standards/api-security-standard.yaml": """apiVersion: codestrata.io/v1alpha1
kind: ArchitectureStandard
metadata:
  id: api-security-standard
  name: API Security Standard
spec:
  status: approved
  scope: apis
  guidance: Authenticate all internal APIs; no secrets in manifests.
""",
    "initiatives/student-modernization.yaml": """apiVersion: codestrata.io/v1alpha1
kind: ModernizationInitiative
metadata:
  id: student-modernization
  name: Student Platform Modernization
spec:
  status: active
  priority: high
  applications:
    - student-information-system
  repositories:
    - student-api
  capabilities:
    - student-registration
  owningTeam: student-platform-team
  objective: Modernize registration services toward cloud-ready runtimes.
""",
    "relationships/core.yaml": """apiVersion: codestrata.io/v1alpha1
kind: Relationships
metadata:
  id: core-relationships
  name: Core Relationships
spec:
  relationships:
    - kind: ORGANIZATION_OWNS_DOMAIN
      source: organization:acme
      target: domain:student-services
    - kind: ORGANIZATION_OWNS_DOMAIN
      source: organization:acme
      target: domain:finance
    - kind: DOMAIN_PROVIDES_CAPABILITY
      source: domain:student-services
      target: capability:student-registration
    - kind: DOMAIN_PROVIDES_CAPABILITY
      source: domain:finance
      target: capability:financial-aid-processing
    - kind: SERVICE_CONSUMES_API
      source: service:registration-service
      target: api:identity-api
    - kind: SERVICE_WRITES_TO_DATA_STORE
      source: service:registration-service
      target: data-store:student-oracle
    - kind: TEAM_OWNS_REPOSITORY
      source: team:student-platform-team
      target: repository:student-api
    - kind: APPLICATION_GOVERNED_BY_STANDARD
      source: application:student-information-system
      target: technology-standard:spring-standard
    - kind: INITIATIVE_MODERNIZES_APPLICATION
      source: initiative:student-modernization
      target: application:student-information-system
""",
}


def seed_university_example(root: Path, *, force: bool = False) -> list[str]:
    created: list[str] = []
    for relative, content in _FILES.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not force:
            continue
        path.write_text(content, encoding="utf-8")
        created.append(relative.replace("\\", "/"))
    return created
