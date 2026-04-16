<template>
  <div class="ai-assistant">
    <header class="ai-header">
      <div class="header-content">
        <div class="chat-info">
          <div class="title-row">
            <h2>AI Assistant</h2>
            <button class="lang-toggle" @click="toggleLanguage">
              {{ language === 'zh' ? '中文' : 'EN' }}
            </button>
          </div>
          <p>Semiconductor packaging expert</p>
        </div>
        <div class="header-actions">
          <div class="chat-avatar">
            <div class="avatar-icon">🤖</div>
          </div>
          <button class="btn-secondary" @click="clearChat">
            <span class="btn-icon">🗑️</span>
            Clear Chat
          </button>
        </div>
      </div>
    </header>
    
    <main class="chat-container">
      
      <div class="chat-messages" ref="chatContainer">
        <div v-for="(message, index) in aiMessages" :key="index" :class="['message', message.type]" animation="fadeIn">
          <div class="message-content">
            <div class="message-header">
              <span class="message-sender">{{ message.sender }}</span>
              <span class="message-time">{{ message.timestamp }}</span>
            </div>
            <div class="message-body">
              <div v-if="message.type === 'user'" class="user-message">
                {{ message.content }}
              </div>
              <div v-else-if="message.type === 'ai'" class="ai-message">
                <div v-if="message.isTyping" class="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <div v-else-if="message.contentType === 'text'" class="ai-text">
                  <div v-html="formatContent(message.content)"></div>
                </div>
                <div v-else-if="message.contentType === 'result'" class="ai-result">
                  <div class="result-section" v-if="message.content.recommended_params.length">
                    <h4>推荐工艺参数</h4>
                    <ul>
                      <li v-for="(param, idx) in message.content.recommended_params" :key="idx">
                        <strong>{{ param.project }}:</strong> {{ param.params }}
                      </li>
                    </ul>
                  </div>
                  <div class="result-section" v-if="message.content.theoretical_suggestions.length">
                    <h4>理论建议</h4>
                    <p>{{ message.content.theoretical_suggestions[0].note }}</p>
                    <ul>
                      <li v-for="(suggestion, idx) in message.content.theoretical_suggestions[0].suggestions" :key="idx">
                        {{ suggestion }}
                      </li>
                    </ul>
                  </div>
                  
                  <!-- LLM分析结果 -->
                  <div class="result-section llm-analysis" v-if="message.llm_analysis">
                    <h4>AI深度分析</h4>
                    <div class="llm-content" v-html="formatContent(message.llm_analysis)"></div>
                  </div>
                  
                  <!-- 本次回答采纳的Main Activity下载 -->
                  <div class="result-section" v-if="message.content.referencedActivities && message.content.referencedActivities.length">
                    <h4>本次回答采纳的案例</h4>
                    <div class="cases-container">
                      <div v-for="(activity, idx) in message.content.referencedActivities" :key="idx" class="case-item">
                        <span class="case-name">{{ activity }}</span>
                        <button class="download-btn" @click="downloadActivityExcel(activity)">
                          <span class="download-icon">📥</span> 下载
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  <!-- 相似历史案例 -->
                  <div class="result-section" v-if="message.content.similar_cases.length">
                    <h4>相似历史案例</h4>
                    <div class="cases-container">
                      <div v-for="(item, idx) in message.content.similar_cases" :key="idx" class="case-item">
                        <span class="case-name">{{ item.project_name }} ({{ item.package_type }})</span>
                        <button class="download-btn" @click="downloadActivityExcel(item.project_name)">
                          <span class="download-icon">📥</span> 下载
                        </button>
                      </div>
                    </div>
                    <div class="download-all-container">
                      <button class="download-all-btn" @click="downloadAllActivitiesExcel">
                        <span class="download-icon">📥</span> 下载所有案例
                      </button>
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
            :placeholder="language === 'zh' ? '询问半导体封装相关问题...' : 'Ask about semiconductor packaging issues...'"
            class="chat-input"
            @keyup.enter="sendMessage"
            :disabled="isLoading"
          />
          <button type="submit" class="btn-primary send-btn" :disabled="isLoading">
            <span class="send-icon">➤</span>
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
export default {
  name: 'AIAssistant',
  data() {
    return {
      messageInput: '',
      aiMessages: [],
      isLoading: false,
      language: 'zh',
      suggestions: [
        'How to reduce warpage in FCBGA packages?',
        'What are the best underfill materials for WLCSP?',
        'How to improve delamination resistance in SiP packages?',
        'What are the key parameters for thermal compression bonding?'
      ]
    }
  },
  mounted() {
    // 添加欢迎消息
    this.addWelcomeMessage()
  },
  methods: {
    addWelcomeMessage() {
      const welcomeMessage = {
        type: 'ai',
        sender: 'AI Assistant',
        content: 'Hello! I am your semiconductor packaging expert. I can help you with issues related to packaging types, materials, failure modes, and DOE experimental design. How can I assist you today?',
        contentType: 'text',
        timestamp: new Date().toLocaleTimeString()
      }
      this.aiMessages.push(welcomeMessage)
    },
    toggleLanguage() {
      this.language = this.language === 'zh' ? 'en' : 'zh'
    },
    async sendMessage() {
      if (!this.messageInput.trim() || this.isLoading) return
      
      const currentTime = new Date().toLocaleTimeString()
      
      // 添加用户消息
      this.aiMessages.push({
        type: 'user',
        sender: 'You',
        content: this.messageInput,
        timestamp: currentTime
      })
      
      // 添加AI正在输入的消息
      const typingMessageIndex = this.aiMessages.length
      this.aiMessages.push({
        type: 'ai',
        sender: 'AI Assistant',
        isTyping: true,
        timestamp: currentTime
      })
      
      const query = this.messageInput
      this.messageInput = ''
      this.isLoading = true
      
      try {
        // 滚动到底部
        this.scrollToBottom()
        
        // 模拟流式输出
        await this.simulateStreamingResponse(query, typingMessageIndex)
        
      } catch (error) {
        console.error('Error sending AI query:', error)
        this.aiMessages[typingMessageIndex] = {
          type: 'ai',
          sender: 'AI Assistant',
          content: 'Error: Failed to get response. Please try again.',
          contentType: 'text',
          timestamp: currentTime
        }
      } finally {
        this.isLoading = false
        this.scrollToBottom()
      }
    },
    async simulateStreamingResponse(query, messageIndex) {
      // 首先发送请求获取完整响应
      const response = await fetch('http://localhost:5000/api/ai/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query, language: this.language })
      })
      
      const data = await response.json()
      
      // 构建完整响应内容，直接显示LLM分析结果
      let fullResponse = data.llm_analysis;
      
      // 模拟流式输出
      this.aiMessages[messageIndex] = {
        type: 'ai',
        sender: 'AI Assistant',
        content: '',
        contentType: 'text',
        timestamp: this.aiMessages[messageIndex].timestamp
      }
      
      let currentIndex = 0
      const typingSpeed = 15 // 打字速度（毫秒/字符）
      
      return new Promise((resolve) => {
        const typingInterval = setInterval(() => {
          if (currentIndex < fullResponse.length) {
            this.aiMessages[messageIndex].content += fullResponse[currentIndex]
            currentIndex++
            this.scrollToBottom()
          } else {
            clearInterval(typingInterval)
            
            // 解析LLM分析结果，提取本次回答采纳的Main Activity
            let referencedActivities = []
            if (data.llm_analysis) {
              // 匹配中文格式
              const zhMatch = data.llm_analysis.match(/## \[本次回答采纳的Main Activity\]\n- (.+?)(?=\n##|$)/s)
              if (zhMatch) {
                referencedActivities = zhMatch[1].trim().split('\n- ').filter(item => item)
              }
              // 匹配英文格式
              const enMatch = data.llm_analysis.match(/## \[Main Activity References\]\n- (.+?)(?=\n##|$)/s)
              if (enMatch) {
                referencedActivities = enMatch[1].trim().split('\n- ').filter(item => item)
              }
            }
            
            // 从相似案例中筛选出被引用的案例
            let filteredSimilarCases = []
            if (referencedActivities.length > 0 && data.rule_based.similar_cases) {
              filteredSimilarCases = data.rule_based.similar_cases.filter(caseItem => 
                referencedActivities.includes(caseItem.project_name)
              )
            } else {
              // 如果没有被引用的案例，不显示任何相似案例
              filteredSimilarCases = []
            }
            
            // 最终替换为完整的结果消息，保持与流式输出一致
            this.aiMessages[messageIndex] = {
              type: 'ai',
              sender: 'AI Assistant',
              content: {
                ...data.rule_based,
                similar_cases: filteredSimilarCases,
                referencedActivities: referencedActivities
              },
              contentType: 'result',
              llm_analysis: data.llm_analysis,
              timestamp: this.aiMessages[messageIndex].timestamp
            }
            
            this.scrollToBottom()
            resolve()
          }
        }, typingSpeed)
      })
    },
    formatContent(content) {
      // 将换行符转换为HTML换行
      let formatted = content.replace(/\n/g, '<br>')
      // 为标题添加样式
      formatted = formatted.replace(/(\d+\.\s+)([^<]+)/g, '<strong>$1$2</strong>')
      return formatted
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
      this.aiMessages = []
      this.addWelcomeMessage()
    },
    useSuggestion(suggestion) {
      this.messageInput = suggestion
      this.sendMessage()
    },
    async downloadActivityExcel(projectName) {
      try {
        // 获取活动列表
        const response = await fetch('http://localhost:5000/api/activities')
        const activities = await response.json()
        
        // 找到对应的活动ID
        const activity = activities.find(act => act.name === projectName)
        if (activity) {
          // 下载Excel文件
          window.open(`http://localhost:5000/api/download/activity/${activity.id}`, '_blank')
        } else {
          console.error('Activity not found:', projectName)
        }
      } catch (error) {
        console.error('Error downloading activity Excel:', error)
      }
    },
    downloadAllActivitiesExcel() {
      // 下载所有活动的Excel文件
      window.open('http://localhost:5000/api/download/all-activities', '_blank')
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
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-color);
  z-index: 100;
  box-sizing: border-box;
  flex-shrink: 0;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  height: var(--header-height);
  gap: var(--spacing-xl);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.btn-icon {
  margin-right: var(--spacing-xs);
  font-size: var(--font-size-md);
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

.chat-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 100%;
  text-align: center;
}

.title-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  justify-content: center;
}

.chat-info h2 {
  margin: 0;
  color: var(--primary-color);
  font-size: var(--font-size-xl);
  line-height: var(--line-height-tight);
  font-weight: var(--font-weight-bold);
}

.lang-toggle {
  background: rgba(0, 212, 255, 0.1);
  color: var(--primary-color);
  border: 1px solid var(--border-primary);
  padding: var(--spacing-xs) var(--spacing-md);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-normal);
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
}

.lang-toggle:hover {
  background: rgba(0, 212, 255, 0.2);
  border-color: var(--primary-color);
  transform: scale(1.05);
  box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
}

.lang-toggle:active {
  transform: scale(0.95);
}

.chat-info p {
  margin: var(--spacing-xs) 0 0 0;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-tight);
}

.chat-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-lg);
  transition: all var(--transition-normal);
}

.chat-avatar:hover {
  transform: scale(1.05);
  box-shadow: var(--shadow-xl);
}

.avatar-icon {
  font-size: var(--font-size-xl);
  font-weight: bold;
  color: white;
}

.message {
  margin-bottom: var(--spacing-lg);
  max-width: 85%;
  animation: messageFadeIn 0.3s ease;
}

@keyframes messageFadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  align-self: flex-end;
  margin-left: auto;
}

.message.ai {
  align-self: flex-start;
}

.message-content {
  padding: var(--spacing-lg);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  font-size: var(--font-size-md);
  position: relative;
  overflow: hidden;
}

.message.user .message-content {
  background: rgba(0, 255, 128, 0.1);
  border: 1px solid var(--border-secondary);
  border-bottom-right-radius: var(--radius-sm);
}

.message.ai .message-content {
  background: var(--surface-secondary);
  border: 1px solid var(--border-primary);
  border-bottom-left-radius: var(--radius-sm);
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

.message-body {
  line-height: var(--line-height-relaxed);
}

.user-message {
  word-wrap: break-word;
}

.ai-message {
  word-wrap: break-word;
}

/* 打字指示器样式 */
.typing-indicator {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) 0;
}

.typing-indicator span {
  width: 10px;
  height: 10px;
  background: var(--primary-color);
  border-radius: 50%;
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

/* 结果部分样式 */
.result-section {
  margin-bottom: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--surface-primary);
  border-radius: var(--radius-md);
  border-left: 4px solid var(--primary-color);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
}

.result-section:hover {
  transform: translateX(4px);
  box-shadow: var(--shadow-md);
}

.result-section h4 {
  margin: 0 0 var(--spacing-md) 0;
  color: var(--primary-color);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
}

.result-section ul {
  margin: 0;
  padding-left: var(--spacing-xl);
}

.cases-container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.case-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm);
  background: var(--surface-tertiary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  transition: all var(--transition-normal);
}

.case-item:hover {
  background: var(--surface-secondary);
  border-color: var(--primary-color);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.case-name {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  flex: 1;
}

.download-btn {
  background: rgba(0, 212, 255, 0.1);
  color: var(--primary-color);
  border: 1px solid var(--border-primary);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-normal);
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  white-space: nowrap;
}

.download-btn:hover {
  background: rgba(0, 212, 255, 0.2);
  border-color: var(--primary-color);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.download-all-container {
  display: flex;
  justify-content: center;
  margin-top: var(--spacing-md);
}

.download-all-btn {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  color: white;
  border: none;
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-normal);
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  white-space: nowrap;
}

.download-all-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-xl);
}

.download-icon {
  font-size: var(--font-size-md);
}

.result-section ul {
  margin: 0;
  padding-left: var(--spacing-xl);
}

.result-section li {
  margin-bottom: var(--spacing-xs);
  line-height: var(--line-height-normal);
  font-size: var(--font-size-md);
}

.result-section li strong {
  color: var(--primary-light);
  font-weight: var(--font-weight-semibold);
}

/* 核心实战经验和其他部分的文本格式化 */
.result-section ul {
  list-style-type: none;
  padding-left: 0;
}

.result-section ul li {
  position: relative;
  padding-left: var(--spacing-lg);
  margin-bottom: var(--spacing-sm);
  line-height: var(--line-height-relaxed);
}

.result-section ul li:before {
  content: "•";
  position: absolute;
  left: 0;
  color: var(--primary-color);
  font-weight: bold;
}

/* 核心实战经验样式 */
.insights-container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.insight-item {
  background: var(--surface-tertiary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  padding: var(--spacing-md);
  transition: all var(--transition-normal);
}

.insight-item:hover {
  background: var(--surface-secondary);
  border-color: var(--primary-color);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.insight-header {
  margin-bottom: var(--spacing-sm);
  color: var(--primary-color);
  font-weight: var(--font-weight-semibold);
}

.insight-content {
  line-height: var(--line-height-relaxed);
  font-size: var(--font-size-md);
  color: var(--text-primary);
}

.result-section li strong {
  color: var(--primary-light);
  font-weight: var(--font-weight-semibold);
}

/* LLM分析结果样式 */
.llm-analysis {
  background: rgba(0, 212, 255, 0.05);
  border-left: 4px solid var(--primary-color);
  padding: var(--spacing-lg);
  border-radius: var(--radius-md);
  margin-top: var(--spacing-md);
  box-shadow: var(--shadow-sm);
}

.llm-content {
  line-height: var(--line-height-relaxed);
  color: var(--text-primary);
  font-size: var(--font-size-md);
}

.llm-content strong {
  color: var(--primary-color);
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--spacing-sm);
  display: block;
}

.llm-content br {
  margin-bottom: var(--spacing-sm);
}

/* 聊天输入区域 */
.chat-input-area {
  background: var(--surface-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  padding: var(--spacing-lg);
  max-height: 220px;
  overflow-y: auto;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
}

.chat-input-area:focus-within {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
}

.input-form {
  display: flex;
  gap: var(--spacing-md);
  align-items: center;
  margin-bottom: var(--spacing-md);
  flex-shrink: 0;
}

.chat-input {
  flex: 1;
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--surface-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  color: var(--text-primary);
  font-size: var(--font-size-md);
  transition: all var(--transition-normal);
  min-width: 0;
}

.chat-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
  background: var(--surface-tertiary);
}

.send-btn {
  border-radius: 50%;
  width: 48px;
  height: 48px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-lg);
  flex-shrink: 0;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  color: white;
  border: none;
  cursor: pointer;
  transition: all var(--transition-normal);
  box-shadow: var(--shadow-md);
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-xl);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: var(--shadow-sm);
}

.send-icon {
  font-size: var(--font-size-lg);
  transition: all var(--transition-normal);
}

.send-btn:hover:not(:disabled) .send-icon {
  transform: scale(1.1);
}

/* 建议区域 */
.suggestions {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
  margin-top: var(--spacing-sm);
}

.suggestion-btn {
  background: var(--surface-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xxl);
  padding: var(--spacing-sm) var(--spacing-md);
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-normal);
  white-space: nowrap;
}

.suggestion-btn:hover {
  background: rgba(0, 212, 255, 0.1);
  border-color: var(--primary-color);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

/* 滚动条样式 */
.chat-messages::-webkit-scrollbar {
  width: 8px;
}

.chat-messages::-webkit-scrollbar-track {
  background: var(--surface-secondary);
  border-radius: var(--radius-sm);
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(0, 212, 255, 0.3);
  border-radius: var(--radius-sm);
  transition: all var(--transition-normal);
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 212, 255, 0.5);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .ai-header {
    padding: var(--spacing-sm) var(--spacing-md);
  }
  
  .header-content {
    gap: var(--spacing-md);
    flex-direction: column;
    height: auto;
    padding: var(--spacing-sm) 0;
  }
  
  .chat-info {
    text-align: center;
  }
  
  .title-row {
    flex-direction: column;
    gap: var(--spacing-sm);
  }
  
  .header-actions {
    flex-direction: column;
    gap: var(--spacing-sm);
    width: 100%;
    align-items: center;
  }
  
  .chat-container {
    padding: var(--spacing-md);
    height: calc(100vh - 180px);
  }
  
  .chat-info h2 {
    font-size: var(--font-size-lg);
  }
  
  .chat-info p {
    font-size: var(--font-size-xs);
  }
  
  .chat-avatar {
    width: 40px;
    height: 40px;
  }
  
  .avatar-icon {
    font-size: var(--font-size-md);
  }
  
  .message {
    max-width: 95%;
  }
  
  .message-content {
    padding: var(--spacing-md);
    font-size: var(--font-size-sm);
  }
  
  .message-header {
    font-size: var(--font-size-xs);
  }
  
  .chat-input {
    padding: var(--spacing-sm) var(--spacing-md);
    font-size: var(--font-size-sm);
  }
  
  .send-btn {
    width: 40px;
    height: 40px;
  }
  
  .suggestions {
    flex-direction: column;
    gap: var(--spacing-xs);
  }
  
  .suggestion-btn {
    width: 100%;
    text-align: left;
    padding: var(--spacing-xs) var(--spacing-sm);
    font-size: var(--font-size-xs);
  }
  
  .chat-input-area {
    padding: var(--spacing-md);
  }
  
  .input-form {
    margin-bottom: var(--spacing-sm);
  }
  
  .btn-secondary {
    font-size: var(--font-size-xs);
    padding: var(--spacing-xs) var(--spacing-sm);
    width: 100%;
  }
  
  .btn-icon {
    font-size: var(--font-size-sm);
  }
  
  .result-section {
    padding: var(--spacing-sm);
  }
  
  .result-section h4 {
    font-size: var(--font-size-md);
  }
  
  .result-section li {
    font-size: var(--font-size-sm);
  }
}

/* 平板设备响应式设计 */
@media (min-width: 769px) and (max-width: 1024px) {
  .chat-container {
    padding: var(--spacing-md);
  }
  
  .chat-messages {
    max-height: calc(100vh - 200px);
  }
  
  .message {
    max-width: 90%;
  }
  
  .header-content {
    gap: var(--spacing-lg);
  }
  
  .result-section {
    padding: var(--spacing-sm);
  }
}
</style>
