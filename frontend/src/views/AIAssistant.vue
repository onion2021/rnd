<template>
  <div class="ai-assistant">
    <header class="ai-header">
      <div class="header-content">
        <div class="chat-info">
          <div class="title-row">
            <h2>AI Assistant</h2>
            <button class="lang-toggle" @click="toggleLanguage" :disabled="isLoading">
              {{ language === 'zh' ? '中文' : 'EN' }}
            </button>
          </div>
          <p>DOE data grounded semiconductor packaging assistant</p>
        </div>

        <div class="header-actions">
          <div class="chat-avatar">
            <div class="avatar-icon">AI</div>
          </div>
          <button class="btn-secondary" @click="clearChat" :disabled="isLoading">
            Clear Chat
          </button>
        </div>
      </div>
    </header>

    <main class="chat-container">
      <div class="chat-messages" ref="chatContainer">
        <div
          v-for="(message, index) in aiMessages"
          :key="index"
          :class="['message', message.type]"
        >
          <div class="message-content">
            <div class="message-header">
              <span class="message-sender">{{ message.sender }}</span>
              <span class="message-time">{{ message.timestamp }}</span>
            </div>

            <div class="message-body">
              <div v-if="message.type === 'user'" class="user-message">
                {{ message.content }}
              </div>

              <div v-else class="ai-message">
                <div v-if="message.isTyping" class="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>

                <div v-else-if="message.contentType === 'text'" class="ai-text">
                  <div v-html="formatContent(message.content)"></div>
                </div>

                <div v-else-if="message.contentType === 'result'" class="ai-result">
                  <div class="result-section llm-analysis" v-if="message.llm_analysis">
                    <h4>{{ language === 'zh' ? 'AI 数据回答' : 'AI Data Answer' }}</h4>
                    <div class="llm-content" v-html="formatContent(message.llm_analysis)"></div>
                  </div>

                  <div
                    class="result-section"
                    v-if="message.content.projectCards && message.content.projectCards.length"
                  >
                    <h4>{{ language === 'zh' ? '相关 Project / DOE' : 'Related Project / DOE' }}</h4>
                    <div class="project-cards">
                      <article
                        v-for="project in message.content.projectCards"
                        :key="project.id"
                        class="project-card"
                        :class="{ expanded: getExpandedRelatedDoe(project) }"
                      >
                        <div class="project-card-header">
                          <div>
                            <p class="project-kicker">Project</p>
                            <h5 class="project-title">
                              {{ project.display_name || project.name }}
                            </h5>
                            <p
                              v-if="project.display_name && project.display_name !== project.name"
                              class="project-subtitle"
                            >
                              {{ project.name }}
                            </p>
                          </div>
                          <span
                            v-if="getProjectDoes(project).length"
                            class="doe-count"
                          >
                            {{ getProjectDoes(project).length }} DOE
                          </span>
                        </div>

                        <div v-if="project.background" class="project-background">
                          <span class="field-label">Background</span>
                          <div class="field-value multiline">{{ project.background }}</div>
                        </div>

                        <div
                          v-if="getProjectDoes(project).length"
                          class="project-does"
                        >
                          <span class="field-label">DOE</span>
                          <div class="doe-chip-list">
                            <button
                              v-for="doe in getProjectDoes(project)"
                              :key="doe.id"
                              type="button"
                              class="doe-chip"
                              :class="{
                                'is-related': isRelatedDoe(project, doe.id),
                                'is-open': project.expandedDoeId === doe.id
                              }"
                              @click="toggleRelatedDoe(index, project.id, doe.id)"
                            >
                              {{ doe.doe_number }}
                            </button>
                          </div>
                        </div>

                        <transition name="expand">
                          <div
                            v-if="getExpandedRelatedDoe(project)"
                            class="doe-panel"
                          >
                            <div class="doe-panel-header">
                              <div class="doe-panel-meta">
                                <span class="doe-pill">
                                  DOE {{ getExpandedRelatedDoe(project).doe_number }}
                                </span>
                                <span
                                  v-if="getExpandedRelatedDoe(project).order"
                                  class="order-pill"
                                >
                                  {{ getExpandedRelatedDoe(project).order }}
                                </span>
                                <span
                                  v-if="getExpandedRelatedDoe(project).activity_flow_doe_number"
                                  class="order-pill"
                                >
                                  Flow {{ getExpandedRelatedDoe(project).activity_flow_doe_number }}
                                </span>
                              </div>
                              <button
                                type="button"
                                class="collapse-button"
                                @click="toggleRelatedDoe(index, project.id, getExpandedRelatedDoe(project).id)"
                              >
                                Hide
                              </button>
                            </div>

                            <div
                              v-if="getExpandedRelatedDoe(project).title"
                              class="doe-title"
                            >
                              {{ getExpandedRelatedDoe(project).title }}
                            </div>

                            <div
                              v-if="getExpandedRelatedDoe(project).detail_fields.length"
                              class="detail-grid"
                            >
                              <div
                                v-for="field in getExpandedRelatedDoe(project).detail_fields"
                                :key="field.key"
                                class="detail-card"
                              >
                                <span class="detail-label">{{ field.label }}</span>
                                <div class="detail-value multiline">{{ field.value }}</div>
                              </div>
                            </div>

                            <section
                              v-if="getExpandedRelatedDoe(project).fixed_factors.length"
                              class="section-block"
                            >
                              <h4 class="section-title">Fixed Factor</h4>
                              <div class="factor-grid">
                                <div
                                  v-for="factor in getExpandedRelatedDoe(project).fixed_factors"
                                  :key="factor.key"
                                  class="factor-card"
                                >
                                  <span class="factor-name">{{ factor.name }}</span>
                                  <div class="factor-condition multiline">{{ factor.condition }}</div>
                                </div>
                              </div>
                            </section>

                            <section
                              v-if="getExpandedRelatedDoe(project).changed_factors.length"
                              class="section-block"
                            >
                              <h4 class="section-title">Changed Factor</h4>
                              <div class="factor-grid">
                                <div
                                  v-for="factor in getExpandedRelatedDoe(project).changed_factors"
                                  :key="factor.key"
                                  class="factor-card changed"
                                >
                                  <span class="factor-name">{{ factor.name }}</span>
                                  <div class="factor-condition multiline">{{ factor.condition }}</div>
                                </div>
                              </div>
                            </section>

                            <section
                              v-if="getExpandedRelatedDoe(project).evaluation_fields.length"
                              class="section-block"
                            >
                              <h4 class="section-title">Additional Results</h4>
                              <div class="factor-grid">
                                <div
                                  v-for="field in getExpandedRelatedDoe(project).evaluation_fields"
                                  :key="field.key"
                                  class="factor-card result"
                                >
                                  <span class="factor-name">{{ field.name }}</span>
                                  <div class="factor-condition multiline">{{ field.condition }}</div>
                                </div>
                              </div>
                            </section>

                            <section
                              v-if="getExpandedRelatedDoe(project).additional_fields.length"
                              class="section-block"
                            >
                              <h4 class="section-title">Additional Info</h4>
                              <div class="detail-grid compact">
                                <div
                                  v-for="field in getExpandedRelatedDoe(project).additional_fields"
                                  :key="field.key"
                                  class="detail-card"
                                >
                                  <span class="detail-label">{{ field.label }}</span>
                                  <div class="detail-value multiline">{{ field.value }}</div>
                                </div>
                              </div>
                            </section>
                          </div>
                        </transition>
                      </article>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="chat-input-area">
        <form @submit.prevent="sendMessage" class="input-form">
          <input
            v-model="messageInput"
            type="text"
            :placeholder="language === 'zh' ? '请输入和 DOE 数据相关的问题…' : 'Ask a question about the DOE data...'"
            class="chat-input"
            @keyup.enter="sendMessage"
            :disabled="isLoading"
          />
          <button type="submit" class="btn-primary send-btn" :disabled="isLoading">
            <span class="send-icon">→</span>
          </button>
        </form>

        <div class="suggestions" v-if="!isLoading">
          <button
            v-for="(suggestion, index) in suggestions"
            :key="index"
            class="suggestion-btn"
            @click="useSuggestion(suggestion)"
          >
            {{ suggestion }}
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import { apiUrl } from '../api'

export default {
  name: 'AIAssistant',
  data() {
    return {
      messageInput: '',
      aiMessages: [],
      isLoading: false,
      language: 'en'
    }
  },
  computed: {
    suggestions() {
      return this.language === 'zh'
        ? [
            'Post ELP Blister 的 DOE 迭代路径和关键结论是什么？',
            'Dry Desmear Outsourcing 中哪几个 DOE 表现最好？',
            '比较 Dry Desmear Outsourcing 和 Dry + Wet Desmear Pathfinding 的结果差异',
            '哪些 DOE 明确提到了铜附着力或 peel strength？'
          ]
        : [
            'What is the DOE progression and key conclusion for Post ELP Blister?',
            'Which DOE performed best in Dry Desmear Outsourcing?',
            'Compare the results of Dry Desmear Outsourcing vs Dry + Wet Desmear Pathfinding',
            'Which DOE explicitly mentions copper adhesion or peel strength?'
          ]

      if (this.language === 'zh') {
        return [
          '如何解决 Post ELP Blister 问题？',
          'Dry Desmear Outsourcing 的 DOE 结论是什么？',
          'Dry + Wet Desmear Pathfinding 哪些 DOE 表现最好？',
          '和铜附着力相关的 DOE 数据有哪些？'
        ]
      }

      return [
        'How to solve Post ELP Blister issues?',
        'What are the DOE conclusions for Dry Desmear Outsourcing?',
        'Which DOE performed best in Dry + Wet Desmear Pathfinding?',
        'Which DOE data is related to copper adhesion?'
      ]
    }
  },
  mounted() {
    this.addWelcomeMessage()
  },
  methods: {
    addWelcomeMessage() {
      const welcomeContent = this.language === 'zh'
        ? '你好，我会严格基于当前 DOE 数据回答你的问题，并在需要时给出相关 Project 和 DOE 编号。'
        : 'Hello. I will answer strictly from the current DOE data and point out the relevant Project and DOE numbers when needed.'

      this.aiMessages.push({
        type: 'ai',
        sender: 'AI Assistant',
        content: welcomeContent,
        contentType: 'text',
        timestamp: new Date().toLocaleTimeString()
      })
    },
    toggleLanguage() {
      if (this.isLoading) return
      this.language = this.language === 'zh' ? 'en' : 'zh'
      this.aiMessages = []
      this.addWelcomeMessage()
    },
    async sendMessage() {
      if (!this.messageInput.trim() || this.isLoading) return

      const currentTime = new Date().toLocaleTimeString()
      const query = this.messageInput

      this.aiMessages.push({
        type: 'user',
        sender: 'You',
        content: query,
        timestamp: currentTime
      })

      const typingMessageIndex = this.aiMessages.length
      this.aiMessages.push({
        type: 'ai',
        sender: 'AI Assistant',
        isTyping: true,
        timestamp: currentTime
      })

      this.messageInput = ''
      this.isLoading = true

      try {
        this.scrollToBottom()
        await this.simulateStreamingResponse(query, typingMessageIndex)
      } catch (error) {
        console.error('Error sending AI query:', error)
        this.aiMessages[typingMessageIndex] = {
          type: 'ai',
          sender: 'AI Assistant',
          content: this.language === 'zh'
            ? '请求失败，请稍后再试。'
            : 'Request failed. Please try again.',
          contentType: 'text',
          timestamp: currentTime
        }
      } finally {
        this.isLoading = false
        this.scrollToBottom()
      }
    },
    async simulateStreamingResponse(query, messageIndex) {
      const response = await fetch(apiUrl('/api/ai/query'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream'
        },
        body: JSON.stringify({ query, language: this.language })
      })

      if (!response.ok) {
        throw new Error('Failed to query AI backend')
      }

      if (!this.aiMessages[messageIndex]) return

      this.aiMessages[messageIndex] = {
        type: 'ai',
        sender: 'AI Assistant',
        content: '',
        contentType: 'text',
        timestamp: this.aiMessages[messageIndex].timestamp
      }

      if (!response.body) {
        throw new Error('Streaming response body is unavailable')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let finalPayload = null

      while (true) {
        const { value, done } = await reader.read()
        buffer += decoder.decode(value || new Uint8Array(), { stream: !done })

        let eventBoundary = buffer.indexOf('\n\n')
        while (eventBoundary !== -1) {
          const rawEvent = buffer.slice(0, eventBoundary)
          buffer = buffer.slice(eventBoundary + 2)
          const parsedEvent = this.parseSseEvent(rawEvent)

          if (parsedEvent?.event === 'message' && parsedEvent.data?.delta) {
            if (!this.aiMessages[messageIndex]) return
            this.aiMessages[messageIndex].content += parsedEvent.data.delta
            this.scrollToBottom()
          } else if (parsedEvent?.event === 'done') {
            finalPayload = parsedEvent.data
          } else if (parsedEvent?.event === 'error') {
            throw new Error(parsedEvent.data?.message || 'Streaming request failed')
          }

          eventBoundary = buffer.indexOf('\n\n')
        }

        if (done) break
      }

      const trailingEvent = this.parseSseEvent(buffer)
      if (trailingEvent?.event === 'done') {
        finalPayload = trailingEvent.data
      } else if (trailingEvent?.event === 'error') {
        throw new Error(trailingEvent.data?.message || 'Streaming request failed')
      }

      if (!this.aiMessages[messageIndex]) return

      const finalText = finalPayload?.llm_analysis || this.aiMessages[messageIndex].content || ''
      this.aiMessages[messageIndex] = {
        type: 'ai',
        sender: 'AI Assistant',
        content: {
          projectCards: this.normalizeProjectCards(finalPayload?.project_cards || [])
        },
        contentType: 'result',
        llm_analysis: finalText,
        timestamp: this.aiMessages[messageIndex].timestamp
      }
      this.scrollToBottom()
    },
    parseSseEvent(rawEvent) {
      const normalized = String(rawEvent || '').trim()
      if (!normalized || normalized.startsWith(':')) return null

      let event = 'message'
      const dataLines = []

      for (const line of normalized.split(/\r?\n/)) {
        if (line.startsWith('event:')) {
          event = line.slice(6).trim()
        } else if (line.startsWith('data:')) {
          dataLines.push(line.slice(5).trimStart())
        }
      }

      if (!dataLines.length) {
        return { event, data: null }
      }

      const rawData = dataLines.join('\n')
      try {
        return {
          event,
          data: JSON.parse(rawData)
        }
      } catch {
        return {
          event,
          data: { raw: rawData }
        }
      }
    },
    formatContent(content) {
      const raw = String(content || '')
      return raw
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/^##\s(.+)$/gm, '<strong>$1</strong>')
        .replace(/^- /gm, '• ')
        .replace(/\n/g, '<br>')
    },
    normalizeProjectCards(projectCards) {
      return projectCards.map(project => {
        const does = Array.isArray(project.does) ? project.does : []
        const relatedDoeIds = Array.isArray(project.related_doe_ids) ? project.related_doe_ids : []
        return {
          ...project,
          does,
          related_doe_ids: relatedDoeIds,
          related_doe_numbers: Array.isArray(project.related_doe_numbers) ? project.related_doe_numbers : [],
          expandedDoeId: null
        }
      })
    },
    getProjectDoes(project) {
      return Array.isArray(project.does) ? project.does : []
    },
    getRelatedDoes(project) {
      const relatedDoeIds = new Set(Array.isArray(project.related_doe_ids) ? project.related_doe_ids : [])
      return this.getProjectDoes(project).filter(doe => relatedDoeIds.has(doe.id))
    },
    isRelatedDoe(project, doeId) {
      return Array.isArray(project.related_doe_ids) && project.related_doe_ids.includes(doeId)
    },
    getExpandedRelatedDoe(project) {
      return this.getProjectDoes(project).find(doe => doe.id === project.expandedDoeId) || null
    },
    toggleRelatedDoe(messageIndex, projectId, doeId) {
      const message = this.aiMessages[messageIndex]
      if (!message || message.contentType !== 'result') return

      this.aiMessages = this.aiMessages.map((entry, index) => {
        if (index !== messageIndex) return entry

        return {
          ...entry,
          content: {
            ...entry.content,
            projectCards: (entry.content.projectCards || []).map(project => {
              if (project.id !== projectId) return project
              return {
                ...project,
                expandedDoeId: project.expandedDoeId === doeId ? null : doeId
              }
            })
          }
        }
      })
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const chatContainer = this.$refs.chatContainer
        if (chatContainer) {
          chatContainer.scrollTop = chatContainer.scrollHeight
        }
      })
    },
    clearChat() {
      if (this.isLoading) return
      this.aiMessages = []
      this.addWelcomeMessage()
    },
    useSuggestion(suggestion) {
      this.messageInput = suggestion
      this.sendMessage()
    }
  }
}
</script>

<style scoped>
.ai-assistant {
  min-height: 100vh;
  background: linear-gradient(135deg, var(--background-primary) 0%, var(--background-secondary) 100%);
  color: var(--text-primary);
  font-family: var(--font-family);
  display: flex;
  flex-direction: column;
  width: 100%;
}

.ai-header {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-xl);
  background: var(--surface-secondary);
  border-bottom: 1px solid var(--border-color);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  max-width: 1400px;
  gap: var(--spacing-xl);
}

.chat-info h2 {
  margin: 0;
  color: var(--primary-color);
  font-size: var(--font-size-xl);
}

.chat-info p {
  margin: var(--spacing-xs) 0 0 0;
  color: var(--text-secondary);
}

.title-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.lang-toggle {
  background: rgba(0, 212, 255, 0.1);
  color: var(--primary-color);
  border: 1px solid var(--border-primary);
  padding: var(--spacing-xs) var(--spacing-md);
  border-radius: var(--radius-full);
  cursor: pointer;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.chat-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: var(--font-weight-bold);
}

.chat-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--spacing-lg);
  box-sizing: border-box;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  min-height: 300px;
  overflow-y: auto;
  margin-bottom: var(--spacing-md);
  padding: var(--spacing-lg);
  background: var(--surface-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
}

.message {
  margin-bottom: var(--spacing-lg);
  max-width: 85%;
}

.message.user {
  margin-left: auto;
}

.message-content {
  padding: var(--spacing-lg);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}

.message.user .message-content {
  background: rgba(0, 255, 128, 0.08);
  border: 1px solid var(--border-secondary);
}

.message.ai .message-content {
  background: var(--surface-secondary);
  border: 1px solid var(--border-primary);
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
  font-size: var(--font-size-sm);
}

.message-sender {
  font-weight: var(--font-weight-semibold);
  color: var(--primary-color);
}

.message-time {
  color: var(--text-tertiary);
  font-size: var(--font-size-xs);
}

.typing-indicator {
  display: flex;
  gap: var(--spacing-xs);
}

.typing-indicator span {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--primary-color);
  animation: typing 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.result-section {
  margin-bottom: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--surface-primary);
  border-radius: var(--radius-md);
  border-left: 4px solid var(--primary-color);
}

.result-section h4 {
  margin: 0 0 var(--spacing-md) 0;
  color: var(--primary-color);
}

.llm-content {
  line-height: var(--line-height-relaxed);
}

.project-cards {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.project-card {
  background:
    linear-gradient(135deg, rgba(0, 212, 255, 0.08), rgba(7, 18, 38, 0.08)),
    var(--surface-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast), transform var(--transition-fast);
}

.project-card.expanded {
  border-color: var(--border-primary);
  box-shadow: 0 0 0 1px rgba(0, 212, 255, 0.22);
}

.project-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-md);
}

.doe-count {
  flex-shrink: 0;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-full);
  background: rgba(0, 212, 255, 0.14);
  color: var(--primary-color);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.project-kicker {
  margin: 0 0 var(--spacing-xs) 0;
  font-size: var(--font-size-xs);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--primary-color);
}

.project-title {
  margin: 0;
  font-size: var(--font-size-lg);
}

.project-subtitle {
  margin: var(--spacing-xs) 0 0 0;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}

.project-background,
.project-does {
  margin-top: var(--spacing-md);
}

.field-label {
  display: block;
  margin-bottom: var(--spacing-xs);
  color: var(--primary-color);
  font-weight: var(--font-weight-semibold);
}

.detail-label,
.factor-name {
  font-weight: var(--font-weight-semibold);
  color: var(--primary-color);
}

.field-value,
.detail-value,
.factor-condition,
.multiline {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

.doe-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.doe-chip,
.collapse-button {
  display: inline-flex;
  align-items: center;
  border-radius: var(--radius-full);
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary);
  padding: 0.45rem 0.9rem;
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.doe-chip:hover,
.collapse-button:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-primary);
  transform: translateY(-1px);
}

.doe-chip.is-related {
  background: rgba(0, 212, 255, 0.18);
  border-color: rgba(0, 212, 255, 0.6);
  color: var(--primary-color);
  box-shadow: 0 0 0 1px rgba(0, 212, 255, 0.12);
}

.doe-chip.is-open {
  border-color: var(--primary-color);
  color: var(--text-primary);
  box-shadow: 0 0 0 1px rgba(0, 212, 255, 0.22);
}

.doe-panel {
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-lg);
  border-top: 1px solid rgba(0, 212, 255, 0.18);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.doe-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-md);
}

.doe-panel-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.doe-pill,
.order-pill {
  display: inline-flex;
  align-items: center;
  border-radius: var(--radius-full);
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: var(--font-size-sm);
}

.doe-pill {
  background: var(--primary-color);
  color: white;
}

.order-pill {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-secondary);
}

.doe-title {
  color: var(--text-primary);
  font-weight: var(--font-weight-semibold);
}

.detail-grid,
.factor-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-md);
}

.detail-grid.compact {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.detail-card,
.factor-card {
  background: var(--surface-primary);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.section-block {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.section-title {
  margin: 0;
  font-size: var(--font-size-lg);
  color: var(--text-primary);
}

.factor-card.changed {
  border-left: 3px solid #f59e0b;
}

.factor-card.result {
  border-left: 3px solid #22c55e;
}

.expand-enter-active,
.expand-leave-active {
  transition: all 0.2s ease;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.chat-input-area {
  background: var(--surface-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  padding: var(--spacing-lg);
}

.input-form {
  display: flex;
  gap: var(--spacing-md);
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.chat-input {
  flex: 1;
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--surface-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  color: var(--text-primary);
}

.chat-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
}

.send-btn {
  border-radius: 50%;
  width: 48px;
  height: 48px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.suggestions {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.suggestion-btn {
  background: var(--surface-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xxl);
  padding: var(--spacing-sm) var(--spacing-md);
  color: var(--text-primary);
  cursor: pointer;
}

.suggestion-btn:hover {
  background: rgba(0, 212, 255, 0.1);
  border-color: var(--primary-color);
}

@media (max-width: 768px) {
  .ai-header {
    padding: var(--spacing-sm) var(--spacing-md);
  }

  .header-content {
    flex-direction: column;
    align-items: stretch;
    gap: var(--spacing-md);
  }

  .title-row,
  .header-actions {
    justify-content: center;
  }

  .chat-container {
    padding: var(--spacing-md);
  }

  .message {
    max-width: 100%;
  }

  .project-card-header,
  .doe-panel-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .detail-grid,
  .detail-grid.compact,
  .factor-grid {
    grid-template-columns: 1fr;
  }

  .input-form {
    align-items: stretch;
  }

  .send-btn {
    width: 44px;
    height: 44px;
    align-self: center;
  }

  .suggestions {
    flex-direction: column;
  }
}
</style>
