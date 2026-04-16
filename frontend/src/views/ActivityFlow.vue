<template>
  <div class="activity-flow">
    <h2 class="page-title">活动流程</h2>
    
    <div class="activity-list">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else>
        <div 
          v-for="activity in activities" 
          :key="activity.id" 
          class="activity-card"
          @click="toggleActivity(activity.id)"
        >
          <div class="activity-header">
            <h3>{{ activity.name }}</h3>
            <span class="toggle-icon">{{ expandedActivity === activity.id ? '▼' : '▶' }}</span>
          </div>
          <div class="activity-background">
            {{ activity.background }}
          </div>
          
          <div v-if="expandedActivity === activity.id" class="sub-activities">
            <h4>子活动</h4>
            <div 
              v-for="sub in activity.sub_activities" 
              :key="sub.id" 
              class="sub-activity-card"
            >
              <div class="sub-activity-header">
                <span class="order">{{ sub.order_num }}.</span>
                <span class="doe-number">{{ sub.doe_number }}</span>
              </div>
              <div class="sub-activity-content">
                <h5>{{ sub.activity_name }}</h5>
                <div class="sub-activity-background">{{ sub.background }}</div>
                <div class="sub-activity-result">{{ sub.result }}</div>
              </div>
            </div>
            
            <div v-if="activity.summary" class="activity-summary">
              <h4>总结</h4>
              <div>{{ activity.summary }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ActivityFlow',
  data() {
    return {
      activities: [],
      loading: true,
      error: null,
      expandedActivity: null
    }
  },
  mounted() {
    this.fetchActivities()
  },
  methods: {
    async fetchActivities() {
      this.loading = true
      this.error = null
      try {
        const response = await fetch('http://localhost:5000/api/activities')
        if (!response.ok) {
          throw new Error('Failed to fetch activities')
        }
        const activities = await response.json()
        
        // 获取每个活动的子活动
        for (const activity of activities) {
          const subResponse = await fetch(`http://localhost:5000/api/activities/${activity.id}`)
          if (subResponse.ok) {
            const activityWithSub = await subResponse.json()
            activity.sub_activities = activityWithSub.sub_activities
          } else {
            activity.sub_activities = []
          }
        }
        
        this.activities = activities
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    toggleActivity(id) {
      this.expandedActivity = this.expandedActivity === id ? null : id
    }
  }
}
</script>

<style scoped>
.activity-flow {
  padding: var(--spacing-lg);
  min-height: 100vh;
}

.page-title {
  font-size: var(--font-size-xl);
  font-weight: bold;
  color: var(--text-primary);
  margin-bottom: var(--spacing-lg);
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.activity-card {
  background: var(--surface-secondary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  cursor: pointer;
  transition: all var(--transition-normal);
  border: 1px solid var(--border-color);
}

.activity-card:hover {
  background: var(--surface-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.activity-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.activity-header h3 {
  font-size: var(--font-size-lg);
  font-weight: bold;
  color: var(--text-primary);
  margin: 0;
}

.toggle-icon {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  transition: transform var(--transition-fast);
}

.activity-background {
  color: var(--text-secondary);
  font-size: var(--font-size-md);
  line-height: 1.5;
  margin-bottom: var(--spacing-md);
}

.sub-activities {
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.sub-activities h4 {
  font-size: var(--font-size-md);
  font-weight: bold;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-sm) 0;
}

.sub-activity-card {
  background: var(--surface-tertiary);
  border-radius: var(--radius-sm);
  padding: var(--spacing-sm);
  border-left: 3px solid var(--primary-color);
}

.sub-activity-header {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xs);
}

.order {
  font-weight: bold;
  color: var(--primary-color);
}

.doe-number {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  background: var(--surface-secondary);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.sub-activity-content {
  margin-top: var(--spacing-xs);
}

.sub-activity-content h5 {
  font-size: var(--font-size-md);
  font-weight: bold;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-xs) 0;
}

.sub-activity-background {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.4;
  margin-bottom: var(--spacing-xs);
}

.sub-activity-result {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.4;
  background: var(--surface-secondary);
  padding: var(--spacing-xs);
  border-radius: var(--radius-sm);
}

.activity-summary {
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm);
  background: var(--surface-tertiary);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--accent-color);
}

.activity-summary h4 {
  font-size: var(--font-size-md);
  font-weight: bold;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-xs) 0;
}

.activity-summary div {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.4;
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

/* 响应式设计 */
@media (max-width: 768px) {
  .activity-flow {
    padding: var(--spacing-md);
  }
  
  .page-title {
    font-size: var(--font-size-lg);
  }
  
  .activity-header h3 {
    font-size: var(--font-size-md);
  }
  
  .activity-background {
    font-size: var(--font-size-sm);
  }
}
</style>