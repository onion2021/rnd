<template>
  <div class="flow-detail">
    <div v-if="loading" class="state-message">Loading project...</div>
    <div v-else-if="error" class="state-message error">{{ error }}</div>
    <div v-else-if="project">
      <button class="back-button" @click="goBack">← Back to Project List</button>

      <header class="detail-header">
        <p class="detail-kicker">Project</p>
        <h1 class="detail-title">{{ project.display_name || project.name }}</h1>
        <p v-if="project.background" class="detail-background">{{ project.background }}</p>
      </header>

      <section class="doe-section" v-for="doe in project.does" :key="doe.id">
        <div class="doe-header">
          <span class="doe-pill">DOE {{ doe.doe_number }}</span>
          <span v-if="doe.order" class="order-pill">{{ doe.order }}</span>
        </div>

        <div class="detail-grid" v-if="doe.detail_fields.length">
          <div v-for="field in doe.detail_fields" :key="field.key" class="detail-card">
            <span class="field-label">{{ field.label }}</span>
            <div class="field-value multiline">{{ field.value }}</div>
          </div>
        </div>

        <div v-if="doe.fixed_factors.length" class="factor-section">
          <h3>Fixed Factor</h3>
          <div class="detail-grid">
            <div v-for="factor in doe.fixed_factors" :key="factor.key" class="detail-card">
              <span class="field-label">{{ factor.name }}</span>
              <div class="field-value multiline">{{ factor.condition }}</div>
            </div>
          </div>
        </div>

        <div v-if="doe.changed_factors.length" class="factor-section">
          <h3>Changed Factor</h3>
          <div class="detail-grid">
            <div v-for="factor in doe.changed_factors" :key="factor.key" class="detail-card changed">
              <span class="field-label">{{ factor.name }}</span>
              <div class="field-value multiline">{{ factor.condition }}</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import { apiUrl } from '../api'

export default {
  name: 'FlowDetail',
  data() {
    return {
      project: null,
      loading: true,
      error: null
    }
  },
  mounted() {
    this.fetchProject()
  },
  methods: {
    async fetchProject() {
      this.loading = true
      this.error = null

      try {
        const id = this.$route.params.id
        const response = await fetch(apiUrl(`/api/project-activities/${id}`))
        if (!response.ok) {
          throw new Error('Failed to fetch project detail')
        }
        this.project = await response.json()
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    goBack() {
      this.$router.push('/flow-list')
    }
  }
}
</script>

<style scoped>
.flow-detail {
  padding: var(--spacing-lg);
  min-height: 100vh;
}

.state-message {
  padding: var(--spacing-lg);
  background: var(--surface-secondary);
  border-radius: var(--radius-md);
}

.state-message.error {
  color: var(--error-color);
  background: rgba(255, 0, 0, 0.08);
}

.back-button {
  margin-bottom: var(--spacing-lg);
  border: 1px solid var(--border-color);
  background: var(--surface-secondary);
  color: var(--text-primary);
  border-radius: var(--radius-full);
  padding: var(--spacing-sm) var(--spacing-md);
  cursor: pointer;
}

.detail-header {
  margin-bottom: var(--spacing-xl);
}

.detail-kicker {
  margin: 0 0 var(--spacing-xs) 0;
  color: var(--primary-color);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.detail-title {
  margin: 0 0 var(--spacing-md) 0;
}

.detail-background {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
  white-space: pre-wrap;
}

.doe-section {
  margin-bottom: var(--spacing-xl);
  background: var(--surface-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.doe-header {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
}

.doe-pill,
.order-pill {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-full);
}

.doe-pill {
  background: var(--primary-color);
  color: white;
}

.order-pill {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-secondary);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-md);
}

.detail-card {
  background: var(--surface-tertiary);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}

.detail-card.changed {
  border-left: 3px solid #f59e0b;
}

.field-label {
  display: block;
  margin-bottom: var(--spacing-xs);
  color: var(--primary-color);
  font-weight: var(--font-weight-semibold);
}

.multiline {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

.factor-section {
  margin-top: var(--spacing-lg);
}

@media (max-width: 768px) {
  .flow-detail {
    padding: var(--spacing-md);
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
