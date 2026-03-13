# Exemplos Práticos - Context Engineer no Cursor

> **Language Navigation / Navegação**
> - [English Reference](#english-reference)
> - [Referência em Português](#referencia-em-portugues)

## English Reference

Practical examples are currently documented in Portuguese. Use browser translation or refer to the Portuguese section below for complete, step-by-step scenarios (E-commerce B2B, Hospital, Fintech, etc.). All instructions follow the same structure: setup, PRD generation, PRP breakdown, Task execution and validation commands. Please check `docs/assets/context_engineer_flow.mmd` / `.png` for the overall flow referenced across the examples.

---

## Referência em Português

## Casos de Uso Reais

Este documento apresenta exemplos práticos de como usar o framework Context Engineer no Cursor para diferentes tipos de projetos.

---

## Exemplo 1: Sistema de E-commerce B2B

### Passo 0: Configuração Inicial

```bash
# 1. Configure as regras globais
code prompts/GLOBAL_ENGINEERING_RULES.json
```

```json
{
 "policies": {
 "language": {
 "explanations": "PT-BR",
 "code_comments_docstrings": "EN-US"
 },
 "performance_budgets": {
 "api_p95_ms": 150,
 "frontend_bundle_kb": 200
 },
 "security_privacy": {
 "lgpd_default": true,
 "pci_dss_required": true,
 "no_pii_in_logs": true
 }
 }
}
```

```bash
# 2. Defina a stack tecnológica
code prompts/PROJECT_STANDARDS.md
```

```markdown
# E-commerce B2B Stack
- Backend: Python 3.11+, FastAPI, SQLModel, PostgreSQL
- Frontend: React 18, TypeScript, Tailwind CSS, Vite
- Pagamentos: Stripe API, PCI DSS compliance
- Infraestrutura: Docker, AWS ECS, RDS
- Observabilidade: OpenTelemetry, DataDog
```

### Passo 1: Geração do PRD

**Input para o Agente PRD 360°:**

```markdown
# Prompt para o Cursor
Carregue o arquivo: prompts/Agente_PRD_360.md

## Inputs:
- Visão: "Marketplace B2B para produtos industriais com foco em automação de compras corporativas"
- Contexto: "Digitalização acelerada pós-pandemia, empresas buscam eficiência em procurement"
- Usuários: "Compradores industriais (40-60 anos), vendedores B2B, administradores de marketplace"
- Restrições: "LGPD compliance, integração com ERPs (SAP, Oracle), PCI DSS para pagamentos"
- Métricas: "GMV R$ 10M em 12 meses, 500 empresas ativas, NPS > 70"
```

**Output Esperado:**

```markdown
# PRD - Marketplace B2B Industrial

## Resumo Executivo
Plataforma digital para conectar fornecedores industriais com compradores corporativos...

## Requisitos Funcionais Priorizados
- FR-001 [MUST]: Cadastro e autenticação de empresas
- FR-002 [MUST]: Catálogo de produtos industriais
- FR-003 [MUST]: Sistema de cotações e propostas
- FR-004 [MUST]: Processamento de pagamentos B2B
- FR-005 [SHOULD]: Integração com ERPs
- FR-006 [SHOULD]: Dashboard de analytics
- FR-007 [COULD]: Chat em tempo real
```

### Passo 2: Geração de PRPs

**Comando no Cursor:**

```bash
# Carregue o prompt do orquestrador
code prompts/Agente_PRP_Orquestrador.md

# Execute com o prd_structured.json gerado
```

**PRPs Gerados:**

```
PRPs/
├── 00_plan.md/.json # Backlog: 7 épicos, 23 features, 45 tasks
├── 01_scaffold.md/.json # Arquitetura Clean + Docker
├── 02_data_model.md/.json # Entidades: Company, Product, Order, Payment
├── 03_api_contracts.md/.json # 15 endpoints REST + GraphQL
├── 04_ux_flows.md/.json # 8 fluxos principais + mobile
├── 05_quality.md/.json # Testes + cobertura 85%
├── 06_observability.md/.json # Métricas de negócio + SLOs
├── 07_security.md/.json # PCI DSS + LGPD compliance
└── 08_ci_cd_rollout.md/.json # Pipeline AWS + feature flags
```

### Passo 3: Execução de Tarefas

**Exemplo de TASK.FR-001 (Autenticação de Empresas):**

```markdown
# TASK.FR-001 - Autenticação de Empresas B2B

## Objetivo
Implementar sistema de autenticação para empresas com CNPJ, incluindo verificação automática na Receita Federal.

## Entradas
- PRPs/01_scaffold.md (estrutura Clean Architecture)
- PRPs/02_data_model.md (entidade Company)
- PRPs/03_api_contracts.md (endpoints /auth/*)

## Implementação Passo a Passo

### 1. Criar Entidade Company
```python
# src/domain/entities/company.py
from sqlmodel import SQLModel, Field
from typing import Optional
import uuid

class Company(SQLModel, table=True):
 id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
 cnpj: str = Field(unique=True, index=True, regex=r'^\d{14}$')
 company_name: str = Field(max_length=255)
 trade_name: Optional[str] = Field(max_length=255)
 email: str = Field(unique=True, index=True)
 is_verified: bool = Field(default=False)
 created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 2. Implementar Serviço de Autenticação
```python
# src/application/services/auth_service.py
from src.domain.entities.company import Company
from src.infrastructure.external.receita_federal import ReceitaFederalAPI

class CompanyAuthService:
 def __init__(self, company_repo: CompanyRepository, rf_api: ReceitaFederalAPI):
 self.company_repo = company_repo
 self.rf_api = rf_api
 
 async def register_company(self, cnpj: str, email: str) -> Company:
 # Verificar CNPJ na Receita Federal
 company_data = await self.rf_api.get_company_data(cnpj)
 
 # Criar empresa
 company = Company(
 cnpj=cnpj,
 company_name=company_data.name,
 email=email
 )
 
 return await self.company_repo.create(company)
```

## Validações
- `pytest tests/auth/ -v`: Todos os testes passando
- `ruff check src/`: 0 erros de linting
- `curl POST /api/v1/auth/register`: Resposta 201
```

**Execução no Cursor:**

```bash
# 1. Carregue a TASK completa
code TASKs/TASK.FR-001.md

# 2. Execute o agente de codificação
# O agente lerá automaticamente TASK.FR-001.json para validações

# 3. Validação automática será executada
pytest tests/auth/ -v
ruff check src/
```

---

## Exemplo 2: Sistema de Gestão Hospitalar

### Configuração Específica

```json
{
 "policies": {
 "security_privacy": {
 "hipaa_compliance": true,
 "lgpd_default": true,
 "encryption_at_rest": true,
 "audit_trail_required": true
 },
 "performance_budgets": {
 "api_p95_ms": 100,
 "critical_alerts_ms": 50
 }
 }
}
```

### PRD Input

```markdown
Visão: "Sistema integrado de gestão hospitalar com foco em segurança e compliance"
Contexto: "Hospital de médio porte, 200 leitos, necessidade de digitalização"
Usuários: "Médicos, enfermeiros, administrativos, pacientes"
Restrições: "HIPAA compliance, LGPD, disponibilidade 99.9%"
```

### Requisitos Críticos Gerados

```markdown
- FR-001 [MUST]: Prontuário eletrônico seguro
- FR-002 [MUST]: Agendamento de consultas
- FR-003 [MUST]: Controle de medicamentos
- FR-004 [MUST]: Faturamento e convênios
- FR-005 [MUST]: Auditoria completa de acessos
```

### TASK Exemplo - Prontuário Eletrônico

```python
# src/domain/entities/medical_record.py
class MedicalRecord(SQLModel, table=True):
 id: uuid.UUID = Field(primary_key=True)
 patient_id: uuid.UUID = Field(foreign_key="patient.id")
 doctor_id: uuid.UUID = Field(foreign_key="doctor.id")
 
 # Dados criptografados
 symptoms: str = Field(encrypted=True) # Custom field type
 diagnosis: str = Field(encrypted=True)
 treatment: str = Field(encrypted=True)
 
 # Auditoria obrigatória
 created_at: datetime = Field(default_factory=datetime.utcnow)
 created_by: uuid.UUID = Field(foreign_key="user.id")
 last_accessed_at: Optional[datetime] = None
 access_log: List[AccessLog] = Relationship()
```

---

## Exemplo 3: Plataforma Educacional

### Stack Tecnológica

```markdown
# Plataforma EAD
- Backend: Node.js 20, Express, Prisma, PostgreSQL
- Frontend: Next.js 14, TypeScript, Tailwind CSS
- Video: AWS MediaConvert, CloudFront
- Real-time: Socket.io, Redis
- Mobile: React Native (futuro)
```

### Requisitos Específicos

```markdown
- FR-001 [MUST]: Streaming de vídeo adaptativo
- FR-002 [MUST]: Sistema de avaliações online
- FR-003 [MUST]: Fórum de discussões
- FR-004 [SHOULD]: Gamificação (pontos, badges)
- FR-005 [COULD]: IA para recomendações
```

### TASK Exemplo - Streaming de Vídeo

```typescript
// src/services/video-streaming.service.ts
export class VideoStreamingService {
 constructor(
 private awsMediaConvert: MediaConvertClient,
 private videoRepository: VideoRepository
 ) {}

 async processVideo(videoFile: File): Promise<ProcessedVideo> {
 // 1. Upload para S3
 const s3Key = await this.uploadToS3(videoFile);
 
 // 2. Criar job de transcodificação
 const job = await this.awsMediaConvert.createJob({
 Queue: process.env.MEDIACONVERT_QUEUE,
 Settings: {
 Inputs: [{ FileInput: s3Key }],
 OutputGroups: [
 // HLS para streaming adaptativo
 this.createHLSOutputGroup(),
 // MP4 para download
 this.createMP4OutputGroup()
 ]
 }
 });

 // 3. Salvar metadados
 return await this.videoRepository.create({
 originalFile: s3Key,
 jobId: job.Job.Id,
 status: 'PROCESSING'
 });
 }
}
```

---

## Exemplo 4: Sistema de PDV (Ponto de Venda)

### Configuração para Varejo

```json
{
 "policies": {
 "performance_budgets": {
 "api_p95_ms": 50,
 "offline_capability": true,
 "sync_interval_ms": 5000
 },
 "hardware_integration": {
 "fiscal_printer": true,
 "barcode_scanner": true,
 "payment_terminal": true
 }
 }
}
```

### Requisitos Críticos

```markdown
- FR-001 [MUST]: Venda com código de barras
- FR-002 [MUST]: Integração com impressora fiscal
- FR-003 [MUST]: Múltiplas formas de pagamento
- FR-004 [MUST]: Funcionamento offline
- FR-005 [MUST]: Sincronização automática
```

### TASK Exemplo - Venda Offline

```typescript
// src/services/offline-sales.service.ts
export class OfflineSalesService {
 private localDB: IndexedDB;
 private syncQueue: SyncQueue;

 async processSale(items: SaleItem[]): Promise<Sale> {
 const sale: Sale = {
 id: uuid(),
 items,
 total: this.calculateTotal(items),
 timestamp: new Date(),
 status: navigator.onLine ? 'SYNCED' : 'PENDING_SYNC'
 };

 // Salvar localmente sempre
 await this.localDB.sales.add(sale);

 // Tentar sincronizar se online
 if (navigator.onLine) {
 try {
 await this.syncToServer(sale);
 sale.status = 'SYNCED';
 } catch (error) {
 // Adicionar à fila de sincronização
 this.syncQueue.add(sale);
 }
 }

 return sale;
 }
}
```

---

## Comandos Úteis por Projeto

### E-commerce B2B
```bash
# Validar integração com ERP
pytest tests/integrations/erp/ -v

# Testar performance de catálogo
ab -n 1000 -c 10 http://localhost:8000/api/v1/products

# Validar PCI DSS
bandit -r src/payments/
```

### Sistema Hospitalar
```bash
# Validar criptografia
pytest tests/security/encryption/ -v

# Testar auditoria
pytest tests/audit/ -v --cov=src/audit

# Validar HIPAA compliance
python scripts/hipaa_check.py
```

### Plataforma Educacional
```bash
# Testar streaming
pytest tests/video/ -v

# Validar performance de vídeo
curl -w "@curl-format.txt" http://localhost:3000/api/videos/stream

# Testar real-time
npm run test:socket
```

### Sistema PDV
```bash
# Testar funcionalidade offline
npm run test:offline

# Validar sincronização
pytest tests/sync/ -v

# Testar integração hardware
python tests/hardware/test_fiscal_printer.py
```

---

## Métricas de Sucesso por Projeto

### E-commerce B2B
- **Performance**: Catálogo carrega em < 2s
- **Conversão**: Taxa de conversão > 3%
- **Integração**: 95% das integrações ERP funcionando
- **Compliance**: 100% LGPD + PCI DSS

### Sistema Hospitalar
- **Disponibilidade**: 99.9% uptime
- **Segurança**: 0 vazamentos de dados
- **Performance**: Prontuário carrega em < 1s
- **Compliance**: 100% HIPAA + LGPD

### Plataforma Educacional
- **Engagement**: Tempo médio > 30min/sessão
- **Performance**: Vídeo inicia em < 3s
- **Qualidade**: 95% satisfação dos alunos
- **Escalabilidade**: Suporta 10k usuários simultâneos

### Sistema PDV
- **Performance**: Venda processada em < 2s
- **Confiabilidade**: 99.99% das vendas sincronizadas
- **Offline**: Funciona 100% offline por 24h
- **Hardware**: 95% compatibilidade com equipamentos

---

## Dicas Específicas por Domínio

### E-commerce
- Use cache Redis para catálogo
- Implemente search com Elasticsearch
- Configure CDN para imagens
- Monitore carrinho abandonado

### Saúde
- Criptografia end-to-end obrigatória
- Logs de auditoria imutáveis
- Backup automático a cada 4h
- Teste de disaster recovery mensal

### Educação
- CDN global para vídeos
- Compressão adaptativa por bandwidth
- Analytics detalhados de engajamento
- Notificações push inteligentes

### Varejo
- Sincronização incremental
- Cache local robusto
- Fallback para modo degradado
- Monitoramento de hardware

---

## Próximos Passos

1. **Escolha seu projeto** baseado nos exemplos
2. **Configure o ambiente** seguindo o Passo 0
3. **Execute o Agente PRD** com seu contexto específico
4. **Gere os PRPs** com o Orquestrador
5. **Implemente as TASKs** uma por vez
6. **Valide continuamente** com os comandos específicos

Cada exemplo pode ser adaptado para suas necessidades específicas, mantendo sempre os princípios do Context Engineering e as regras de negócio dos PRPs.
