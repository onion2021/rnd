<template>
  <div class="activity-list">
    <h2 class="page-title">Activity List</h2>
    
    <div class="activity-cards">
      <div v-if="loading" class="loading">Loading...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else>
        <div 
          v-for="activity in activities" 
          :key="activity.id" 
          class="activity-card"
          @click="viewActivityDetail(activity.id)"
        >
          <div class="activity-header">
            <h3>{{ activity.name }}</h3>
            <span class="arrow-icon">→</span>
          </div>
          <div class="activity-background">
            {{ activity.background }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ActivityList',
  data() {
    return {
      activities: [],
      loading: true,
      error: null
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
        
        this.activities = activities
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    viewActivityDetail(id) {
      this.$router.push(`/activity-detail/${id}`)
    }
  }
}
</script>

<style scoped>
.activity-list {
  padding: var(--spacing-lg);
  min-height: 100vh;
}

.page-title {
  font-size: var(--font-size-xl);
  font-weight: bold;
  color: var(--text-primary);
  margin-bottom: var(--spacing-lg);
}

.activity-cards {
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

.arrow-icon {
  font-size: var(--font-size-xl);
  color: var(--primary-color);
  transition: transform var(--transition-fast);
}

.activity-card:hover .arrow-icon {
  transform: translateX(4px);
}

.activity-background {
  color: var(--text-secondary);
  font-size: var(--font-size-md);
  line-height: 1.5;
  margin-bottom: var(--spacing-md);
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

/* Responsive design */
@media (max-width: 768px) {
  .activity-list {
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