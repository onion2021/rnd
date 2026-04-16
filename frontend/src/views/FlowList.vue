<template>
  <div class="flow-list">
    <h2 class="page-title">Flow List</h2>
    
    <div class="flow-cards">
      <div v-if="loading" class="loading">Loading...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else>
        <div 
          v-for="activity in activities" 
          :key="activity.id" 
          class="flow-card"
          @click="viewFlowDetail(activity.id)"
        >
          <div class="flow-header">
            <h3>{{ activity.name }}</h3>
            <span class="arrow-icon">→</span>
          </div>
          <div class="flow-background">
            {{ activity.background }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FlowList',
  data() {
    return {
      activities: [],
      loading: true,
      error: null
    }
  },
  mounted() {
    this.fetchFlows()
  },
  methods: {
    async fetchFlows() {
      this.loading = true
      this.error = null
      try {
        const response = await fetch('http://localhost:5000/api/activities')
        if (!response.ok) {
          throw new Error('Failed to fetch flows')
        }
        const activities = await response.json()
        
        this.activities = activities
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    viewFlowDetail(id) {
      this.$router.push(`/flow-detail/${id}`)
    }
  }
}
</script>

<style scoped>
.flow-list {
  padding: var(--spacing-lg);
  min-height: 100vh;
}

.page-title {
  font-size: var(--font-size-xl);
  font-weight: bold;
  color: var(--text-primary);
  margin-bottom: var(--spacing-lg);
}

.flow-cards {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.flow-card {
  background: var(--surface-secondary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  cursor: pointer;
  transition: all var(--transition-normal);
  border: 1px solid var(--border-color);
}

.flow-card:hover {
  background: var(--surface-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.flow-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.flow-header h3 {
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

.flow-card:hover .arrow-icon {
  transform: translateX(4px);
}

.flow-background {
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
  .flow-list {
    padding: var(--spacing-md);
  }
  
  .page-title {
    font-size: var(--font-size-lg);
  }
  
  .flow-header h3 {
    font-size: var(--font-size-md);
  }
  
  .flow-background {
    font-size: var(--font-size-sm);
  }
}
</style>