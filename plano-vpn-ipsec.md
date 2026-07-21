# Plano de Automação — VPN IPSec entre FortiGate e Palo Alto

> Documento de planejamento referente à **Parte 2** do Desafio de Automação — Laboratório de Candidatos (Networking Mercado Livre). Conforme especificado no desafio, não é esperada uma simulação funcional desta VPN; este documento cobre o planejamento teórico e técnico da automação.

---

## 1. Definição de Parâmetros

### 1.1 Topologia geral
[Rede Local A]---[FortiGate]===INTERNET===[Palo Alto]---[Rede Local B]
10.10.10.0/24 WAN: 100.100.100.1 WAN: 200.200.200.1 10.20.20.0/24

### 1.2 Endereços WAN (exemplo)

| Dispositivo | Papel   | IP WAN (exemplo) |
|-------------|---------|-------------------|
| FortiGate   | Ponta A | 100.100.100.1     |
| Palo Alto   | Ponta B | 200.200.200.1     |

### 1.3 Redes locais protegidas por cada lado

| Lado      | Rede Local    |
|-----------|----------------|
| FortiGate | 10.10.10.0/24  |
| Palo Alto | 10.20.20.0/24  |

### 1.4 Rede de túnel (interface tunnel / VTI)

- **Rede:** `169.255.1.0/30`
- **IP do lado FortiGate:** `169.255.1.1/30`
- **IP do lado Palo Alto:** `169.255.1.2/30`

Essa rede /30 endereça a interface de túnel virtual (VTI) em ambas as pontas, permitindo roteamento entre as redes locais através de uma interface roteável, em vez de depender apenas de VPN baseada em política.

### 1.5 Propostas de Fase 1 (IKE) — compatíveis entre fabricantes

| Parâmetro | Valor proposto |
|---|---|
| Versão IKE | IKEv2 |
| Criptografia | AES-256 |
| Hash | SHA-256 |
| Grupo Diffie-Hellman | Grupo 14 (2048-bit) |
| Autenticação | Pre-shared Key (PSK) |
| Lifetime | 28800 segundos (8h) |

### 1.6 Propostas de Fase 2 (IPSec) — compatíveis entre fabricantes

| Parâmetro | Valor proposto |
|---|---|
| Protocolo | ESP |
| Criptografia | AES-256 |
| Hash | SHA-256 |
| PFS | Habilitado (Grupo 14) |
| Lifetime | 3600 segundos (1h) |

> **Nota técnica:** IKEv2 + AES-256 + SHA-256 + DH14 é amplamente suportado tanto no FortiOS quanto no PAN-OS, minimizando risco de incompatibilidade entre fabricantes.

---

## 2. Identificação de Ferramentas/APIs

### 2.1 FortiGate (Fortinet)

| Ferramenta/API | Descrição |
|---|---|
| FortiOS REST API | API nativa, cria/consulta/altera objetos via HTTP, autenticação por token/sessão. Recomendada. |
| pyFG / fortiosapi | Bibliotecas Python que encapsulam a REST API. |
| SSH + CLI scripting | Via Netmiko/Paramiko; mais simples, porém mais frágil a mudanças de versão. |
| FortiManager | Gerenciamento centralizado; útil para múltiplos dispositivos. |

### 2.2 Palo Alto Networks

| Ferramenta/API | Descrição |
|---|---|
| PAN-OS XML API | API nativa baseada em XML, requer API Key. |
| pan-os-python | SDK oficial, abstrai a XML API em objetos Python. Recomendado. |
| Terraform (provider panos) | Infraestrutura como código, útil em pipelines CI/CD. |
| Panorama | Gerenciamento centralizado de múltiplos firewalls Palo Alto. |

### 2.3 Ferramenta escolhida para este planejamento

- **FortiGate:** `fortiosapi` ou requisições HTTP diretas via `requests`.
- **Palo Alto:** SDK oficial `pan-os-python`.

Essa combinação evita a fragilidade de scripts baseados em CLI e se alinha à prática de mercado para automação multi-vendor.

> **Nota de segurança:** credenciais e API Keys de ambos os fabricantes devem ser armazenadas fora do código-fonte (variáveis de ambiente ou cofre de segredos), nunca hardcoded no script — mesma prática recomendada para o switch Cisco na Parte 1.

---

## 3. Passos de Automação

### 3.1 Etapa 1 — Autenticação nas APIs
- FortiGate: autenticação via usuário/senha ou token, obtendo sessão válida.
- Palo Alto: geração de API Key via `type=keygen`.

### 3.2 Etapa 2 — Criação de objetos de rede
- Cadastro das redes locais remotas como "address objects" em cada lado.
- Cadastro do IP do peer remoto.

### 3.3 Etapa 3 — Configuração da Fase 1 (IKE Gateway)
- Configuração do IKE Gateway/Phase1 Interface com IP do peer, interface WAN, parâmetros da Seção 1.5 e a mesma Pre-Shared Key nos dois lados.

### 3.4 Etapa 4 — Configuração da Fase 2 (IPSec Tunnel)
- Configuração do túnel associado ao IKE Gateway, com parâmetros da Seção 1.6.
- Configuração da interface de túnel (VTI) com os IPs definidos na Seção 1.4.

> **Ponto crítico:** os "Proxy-IDs" (Palo Alto) / seletores de tráfego (redes locais definidas na Fase 2) precisam corresponder exatamente entre os dois lados — é a causa mais comum de túneis que estabelecem a Fase 1 com sucesso, mas falham na Fase 2, em ambientes multi-vendor.

### 3.5 Etapa 5 — Rotas
- Rota estática em cada lado apontando para a rede remota via interface de túnel.

### 3.6 Etapa 6 — Políticas de Firewall
- Regras permitindo tráfego entre as redes locais nos dois sentidos, via interface de túnel.

### 3.7 Etapa 7 — Ativação e verificação inicial
- Commit obrigatório no Palo Alto; aplicação imediata no FortiGate.
- Aguardar negociação automática da Fase 1/2.

### 3.8 Etapa 8 — Validação
- Detalhada na Seção 5.

---

## 4. Considerações Específicas

### 4.1 Nomenclatura e conceitos diferentes

| Conceito | FortiGate | Palo Alto |
|---|---|---|
| Fase 1 | `phase1-interface` | `IKE Gateway` |
| Fase 2 | `phase2-interface` | `IPSec Tunnel` |
| Interface de túnel | `ipsec` | `tunnel.x` |

### 4.2 Ordem de negociação e papel ativo/passivo
Definir explicitamente iniciador/respondedor evita ambiguidade na negociação IKE, especialmente com NAT ou IP dinâmico.

### 4.3 Interoperabilidade de algoritmos
Parâmetros escolhidos na Seção 1 priorizam o "mínimo denominador comum" amplamente suportado entre os dois fabricantes.

### 4.4 Sincronização de commits
Palo Alto exige commit explícito; o script precisa considerar esse tempo antes de validar.

### 4.5 Tratamento de erros específico por fabricante
FortiGate retorna JSON com códigos HTTP; Palo Alto retorna XML com atributo `status`. Duas rotinas de tratamento distintas seriam necessárias.


---

## 5. Validação de Configuração e Alertas

### 5.1 O que validar

| Item | Como validar |
|---|---|
| Fase 1 (IKE) | Status via API — deve estar "up"/"established" |
| Fase 2 (IPSec) | Security Associations ativas, com tráfego > 0 |
| Roteamento | Rota estática presente e ativa em ambos os lados |
| Conectividade fim a fim | Teste de ping entre hosts das redes locais A e B |
| Políticas de firewall | Regras ativas e na ordem correta |

### 5.2 Métodos de verificação por fabricante

- **FortiGate:** endpoint `/api/v2/monitor/vpn/ipsec` (ou `get vpn ipsec tunnel summary` via CLI).
- **Palo Alto:** operational commands `<show><vpn><ike-sa></ike-sa></vpn></show>` e `<ipsec-sa>` via XML API.

### 5.3 Estratégia de alertas

1. Consultar status em ambos os lados após aplicar a configuração.
2. Se Fase 1 falhar, alertar especificando o lado e possível causa (ex: PSK ou parâmetros de criptografia divergentes).
3. Se Fase 1 subir mas Fase 2 falhar, alertar separadamente (geralmente indica incompatibilidade de proxy-id/redes locais).
4. Se ambas as fases subirem mas o teste fim a fim falhar, alertar sobre possível problema de rota ou política de firewall.
5. Alertas exibidos de forma agregada ao final da execução.

### 5.4 Observação sobre timing

Devido ao commit obrigatório no Palo Alto (Seção 4.4), a validação deve incluir espera controlada (retry com backoff) após o commit, evitando falsos alertas de "túnel down".