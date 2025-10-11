# 📘 README – Biblioteca de Conhecimento (knowledge_base)
**Projeto:** Synapse.IA – SAAB / TJSP  
**Versão:** 1.0 – Outubro/2025  
**Responsável técnico:** Equipe de Governança e Inovação – SAAB-7  
**Repositório:** `synapse-ia-next`

---

## 🧭 1. Finalidade da Biblioteca

A pasta `knowledge_base/` contém a **base de conhecimento textual** utilizada pelos agentes do ecossistema **Synapse.IA**, incluindo validadores, copilotos e o orquestrador principal.  
Seu objetivo é permitir que os agentes acessem **conteúdo normativo, técnico e institucional revisado** para enriquecer as análises, gerar artefatos aderentes às diretrizes do TJSP e oferecer suporte contextual às etapas do processo licitatório e de gestão administrativa.

---

## 🗂️ 2. Estrutura Geral

```
knowledge_base/
├── DFD/                      → Modelos e diretrizes de Documento de Formalização da Demanda
├── ETP/                      → Estudos Técnicos Preliminares (exemplos e referenciais)
├── TR/                       → Termos de Referência e especificações técnicas
├── instrucoes_normativas/    → Atos normativos internos aplicáveis à SAAB
├── legislacao/               → Normas federais e estaduais (Leis, Decretos, Portarias, Resoluções CNJ)
├── manuais_modelos/          → Guias e modelos institucionais de artefatos padronizados
├── notas_tecnicas/           → Notas técnicas e pareceres de caráter explicativo
└── referencias_internas/     → Reservada a documentos internos e instruções complementares (.gitkeep)
```

---

## 🧩 3. Padrões de Arquivo

- Todos os documentos estão no formato **`.txt`**, convertidos automaticamente a partir de fontes originais em `.docx` e `.pdf`.  
- O encoding padrão é **UTF-8**, garantindo compatibilidade entre sistemas operacionais.  
- O conteúdo é pré-processado e normalizado para leitura semântica por agentes de IA.  
- Cada arquivo contém apenas **texto plano**, sem formatação, garantindo maior desempenho na vetorização e indexação semântica.

---

## ⚙️ 4. Utilização pelos Agentes Synapse.IA

Os módulos principais (`synapse_chat.py` e `validator_engine.py`) são configurados para:
- Ler o conteúdo dos arquivos `.txt` dentro de `knowledge_base/`;  
- Extrair conhecimento contextual durante a execução dos agentes;  
- Enriquecer a geração de minutas, relatórios e checklists validados;  
- Apoiar respostas fundamentadas com base normativa e documental.

---

## 🧱 5. Governança e Atualizações

| Item | Responsável | Frequência | Procedimento |
|------|--------------|-------------|---------------|
| **Inclusão de novos documentos** | SAAB-7 (Governança) | Sob demanda | Converter para `.txt` e subir via push ou upload |
| **Revisão de conteúdo** | SAAB-7 + Diretoria demandante | Semestral | Substituir versões obsoletas mantendo histórico em commit |
| **Expansão da base** | Coordenação do Projeto Synapse.IA | Contínua | Incluir novas pastas temáticas conforme novos agentes forem criados |
| **Validação de integridade** | Desenvolvedor principal (POC Synapse.IA) | A cada atualização do modelo | Executar script de verificação e logar resultados no repositório |

---

## 📥 6. Processo de Atualização (Manual ou via Script)

### 🔹 Atualização manual (recomendada para documentos novos)
1. Converter o documento original (`.docx` ou `.pdf`) em `.txt`;  
2. Conferir o conteúdo textual no bloco de notas (sem caracteres estranhos);  
3. Fazer o upload para a subpasta correspondente;  
4. Inserir mensagem de commit no formato:
   ```
   Atualiza [nome do documento] – [área de conhecimento]
   Exemplo: Atualiza ETP modelo – Área de Engenharia
   ```

### 🔹 Atualização automatizada (opcional)
Utilizar o script `convert_to_txt_v2.py` localizado no ambiente local, conforme padrão:
```bash
python convert_to_txt_v2.py
```
Os arquivos serão atualizados e colocados em `/converted_txt/`, prontos para novo push.

---

## 🔍 7. Auditoria e Controle de Versão

- Cada inclusão ou atualização de arquivo deve gerar **commit individualizado**;  
- Recomenda-se adotar convenção de mensagens:
  ```
  [Área] – [Tipo de documento] – [Breve descrição]
  Exemplo: ETP – Contratação de software – modelo base
  ```
- Alterações relevantes (exclusão, substituição, revisão técnica) devem ser documentadas no histórico de commits.

---

## 🧠 8. Próximas Integrações Planejadas

| Integração | Descrição | Status |
|-------------|------------|--------|
| Leitura dinâmica no Synapse Chat | Agente acessará a biblioteca ao gerar artefatos | 🔄 Em desenvolvimento |
| Indexação semântica via embeddings | Criação de banco vetorial para busca contextual | 🧩 Planejado |
| Painel de governança da biblioteca | Visualização e monitoramento via Streamlit | 🚀 Em prototipagem |

---

## 🔒 9. Observações de Segurança e Conformidade

- Esta biblioteca contém apenas **documentos públicos ou de uso interno não sigiloso**;  
- Documentos restritos devem permanecer armazenados em ambiente protegido (OneDrive institucional);  
- Todo o conteúdo segue as diretrizes de **governança documental** e **Lei nº 14.129/2021** (Governo Digital).

---

## 🧾 10. Histórico

| Versão | Data | Autor | Descrição |
|---------|------|--------|-----------|
| 1.0 | 10/10/2025 | C.D. Mattos | Criação inicial da biblioteca de conhecimento e estruturação das pastas |
