<template>
  <div class="activity-detail">
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="activity">
      <div class="back-button" @click="goBack">
        ← Back to Activity List
      </div>
      
      <div class="activity-header">
        <h1 class="activity-title">{{ activity.name }}</h1>
        <div class="activity-meta">
          <span class="meta-item">ID: {{ activity.id }}</span>
          <span class="meta-item">Created: {{ formatDate(activity.created_at) }}</span>
        </div>
      </div>
      
      <div class="activity-content">
        <div class="section">
          <h2 class="section-title">Background</h2>
          <div class="section-content">{{ activity.background }}</div>
        </div>
        
        <div v-if="activity.sub_activities && activity.sub_activities.length > 0" class="section">
          <h2 class="section-title">Activity Flow</h2>
          <div class="flow-container">
            <div 
              v-for="(sub, index) in activity.sub_activities" 
              :key="sub.id" 
              class="flow-item"
            >
              <div class="flow-number">{{ sub.order_num }}</div>
              <div class="flow-content">
                <div class="flow-header">
                  <span class="doe-number">{{ sub.doe_number }}</span>
                </div>
                <h3 class="flow-title">{{ sub.activity_name }}</h3>
                <div class="flow-background">{{ sub.background }}</div>
                <div class="flow-result">
                  <h4>Result</h4>
                  <div>{{ sub.result }}</div>
                </div>
              </div>
              <div v-if="index < activity.sub_activities.length - 1" class="flow-arrow">↓</div>
            </div>
          </div>
        </div>
        
        <div v-if="activity.summary" class="section">
          <h2 class="section-title">Summary</h2>
          <div class="section-content">{{ activity.summary }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { apiUrl } from '../api'

export default {
  name: 'ActivityDetail',
  data() {
    return {
      activity: null,
      loading: true,
      error: null
    }
  },
  mounted() {
    this.fetchActivityDetail()
  },
  methods: {
    async fetchActivityDetail() {
      this.loading = true
      this.error = null
      try {
        const id = this.$route.params.id
        const response = await fetch(apiUrl(`/api/activities/${id}`))
        if (!response.ok) {
          throw new Error('Failed to fetch activity detail')
        }
        this.activity = await response.json()
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    formatDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    },
    goBack() {
      this.$router.push('/activity-list')
    }
  }
}
</script>

<style scoped>
.activity-detail {
  padding: var(--spacing-lg);
  min-height: 100vh;
}

.loading {
  text-align: center;
  padding: var(--spacing-lg);
  color: var(--text-secondary);
}

.error {
  text-align: center;
  padding: var(--spacing-lg);
  color: var(--error-color);
  background: rgba(255, 0, 0, 0.1);
  border-radius: var(--radius-md);
}

.back-button {
  display: inline-block;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--surface-secondary);
  color: var(--text-primary);
  border-radius: var(--radius-sm);
  cursor: pointer;
  margin-bottom: var(--spacing-lg);
  transition: all var(--transition-fast);
}

.back-button:hover {
  background: var(--surface-hover);
  transform: translateX(-4px);
}

.activity-header {
  margin-bottom: var(--spacing-xl);
}

.activity-title {
  font-size: var(--font-size-xxl);
  font-weight: bold;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-md) 0;
}

.activity-meta {
  display: flex;
  gap: var(--spacing-md);
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}

.meta-item {
  background: var(--surface-secondary);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
}

.activity-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.section {
  background: var(--surface-secondary);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  border: 1px solid var(--border-color);
}

.section-title {
  font-size: var(--font-size-lg);
  font-weight: bold;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-md) 0;
  border-bottom: 2px solid var(--primary-color);
  padding-bottom: var(--spacing-sm);
}

.section-content {
  color: var(--text-secondary);
  line-height: 1.6;
  white-space: pre-wrap;
}

.flow-container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.flow-item {
  display: flex;
  gap: var(--spacing-md);
  align-items: flex-start;
}

.flow-number {
  flex-shrink: 0;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-color);
  color: white;
  font-size: var(--font-size-xl);
  font-weight: bold;
  border-radius: 50%;
  box-shadow: var(--shadow-md);
}

.flow-content {
  flex: 1;
  background: var(--surface-tertiary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border-left: 4px solid var(--primary-color);
}

.flow-header {
  margin-bottom: var(--spacing-sm);
}

.doe-number {
  display: inline-block;
  background: var(--primary-color);
  color: white;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  font-weight: bold;
}

.flow-title {
  font-size: var(--font-size-lg);
  font-weight: bold;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-sm) 0;
}

.flow-background {
  color: var(--text-secondary);
  font-size: var(--font-size-md);
  line-height: 1.5;
  margin-bottom: var(--spacing-md);
}

.flow-result {
  background: var(--surface-secondary);
  padding: var(--spacing-sm);
  border-radius: var(--radius-sm);
  margin-top: var(--spacing-sm);
}

.flow-result h4 {
  font-size: var(--font-size-md);
  font-weight: bold;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-xs) 0;
}

.flow-result > div {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.4;
}

.flow-arrow {
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: var(--font-size-xxl);
  color: var(--primary-color);
  margin: var(--spacing-md) 0;
}

/* Responsive design */
@media (max-width: 768px) {
  .activity-detail {
    padding: var(--spacing-md);
  }
  
  .activity-title {
    font-size: var(--font-size-xl);
  }
  
  .activity-meta {
    flex-direction: column;
    gap: var(--spacing-sm);
  }
  
  .flow-item {
    flex-direction: column;
  }
  
  .flow-number {
    width: 50px;
    height: 50px;
    font-size: var(--font-size-lg);
  }
}
</style>