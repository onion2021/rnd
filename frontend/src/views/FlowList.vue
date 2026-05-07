<template>
  <div class="project-list">
    <h2 class="page-title">Project List</h2>

    <div v-if="loading" class="state-message">Loading projects...</div>
    <div v-else-if="error" class="state-message error">{{ error }}</div>
    <div v-else class="project-cards">
      <article
        v-for="project in projects"
        :key="project.id"
        class="project-card"
      >
        <div class="project-card-header">
          <div>
            <p class="project-kicker">Project</p>
            <h3 class="project-title">{{ project.display_name || project.name }}</h3>
            <p
              v-if="project.display_name && project.display_name !== project.name"
              class="project-subtitle"
            >
              {{ project.name }}
            </p>
          </div>
          <span class="doe-count">{{ project.does.length }} DOE</span>
        </div>

        <div class="project-summary">
          <div class="summary-row">
            <span class="summary-label">Project Name</span>
            <span class="summary-value">{{ project.display_name || project.name }}</span>
          </div>

          <div class="summary-row">
            <span class="summary-label">Background</span>
            <span class="summary-value multiline">{{ project.background }}</span>
          </div>

          <div class="summary-row doe-row">
            <span class="summary-label">DOE</span>
            <div class="doe-chip-list">
              <button
                v-for="doe in project.does"
                :key="doe.id"
                type="button"
                class="doe-chip"
                :class="{ active: getExpandedDoeId(project.id) === doe.id }"
                @click="toggleDoe(project.id, doe.id)"
              >
                {{ doe.doe_number }}
              </button>
            </div>
          </div>
        </div>

        <transition name="expand">
          <div
            v-if="getExpandedDoe(project)"
            class="doe-panel"
          >
            <div class="doe-panel-header">
              <div class="doe-panel-meta">
                <span class="doe-pill">DOE {{ getExpandedDoe(project).doe_number }}</span>
                <span
                  v-if="getExpandedDoe(project).order"
                  class="order-pill"
                >
                  {{ getExpandedDoe(project).order }}
                </span>
              </div>
              <button
                type="button"
                class="collapse-button"
                @click="toggleDoe(project.id, getExpandedDoe(project).id)"
              >
                Hide
              </button>
            </div>

            <div
              v-if="getExpandedDoe(project).detail_fields.length"
              class="detail-grid"
            >
              <div
                v-for="field in getExpandedDoe(project).detail_fields"
                :key="field.key"
                class="detail-card"
              >
                <span class="detail-label">{{ field.label }}</span>
                <div class="detail-value multiline">{{ field.value }}</div>
              </div>
            </div>

            <section
              v-if="getExpandedDoe(project).fixed_factors.length"
              class="section-block"
            >
              <h4 class="section-title">Fixed Factor</h4>
              <div class="factor-grid">
                <div
                  v-for="factor in getExpandedDoe(project).fixed_factors"
                  :key="factor.key"
                  class="factor-card"
                >
                  <span class="factor-name">{{ factor.name }}</span>
                  <div class="factor-condition multiline">{{ factor.condition }}</div>
                </div>
              </div>
            </section>

            <section
              v-if="getExpandedDoe(project).changed_factors.length"
              class="section-block"
            >
              <h4 class="section-title">Changed Factor</h4>
              <div class="factor-grid">
                <div
                  v-for="factor in getExpandedDoe(project).changed_factors"
                  :key="factor.key"
                  class="factor-card changed"
                >
                  <span class="factor-name">{{ factor.name }}</span>
                  <div class="factor-condition multiline">{{ factor.condition }}</div>
                </div>
              </div>
            </section>

            <section
              v-if="getExpandedDoe(project).evaluation_fields.length"
              class="section-block"
            >
              <h4 class="section-title">Additional Results</h4>
              <div class="factor-grid">
                <div
                  v-for="field in getExpandedDoe(project).evaluation_fields"
                  :key="field.key"
                  class="factor-card result"
                >
                  <span class="factor-name">{{ field.name }}</span>
                  <div class="factor-condition multiline">{{ field.condition }}</div>
                </div>
              </div>
            </section>

            <section
              v-if="getExpandedDoe(project).additional_fields.length"
              class="section-block"
            >
              <h4 class="section-title">Additional Info</h4>
              <div class="detail-grid compact">
                <div
                  v-for="field in getExpandedDoe(project).additional_fields"
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
</template>

<script>
import { apiUrl } from '../api'

export default {
  name: 'FlowList',
  data() {
    return {
      projects: [],
      expandedDoeByProject: {},
      loading: true,
      error: null
    }
  },
  mounted() {
    this.fetchProjects()
  },
  methods: {
    async fetchProjects() {
      this.loading = true
      this.error = null

      try {
        const response = await fetch(apiUrl('/api/project-activities'))
        if (!response.ok) {
          throw new Error('Failed to fetch project list')
        }

        this.projects = await response.json()
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    getExpandedDoeId(projectId) {
      return this.expandedDoeByProject[projectId] || null
    },
    getExpandedDoe(project) {
      const expandedDoeId = this.getExpandedDoeId(project.id)
      return project.does.find(doe => doe.id === expandedDoeId) || null
    },
    toggleDoe(projectId, doeId) {
      const currentDoeId = this.getExpandedDoeId(projectId)
      this.expandedDoeByProject = {
        ...this.expandedDoeByProject,
        [projectId]: currentDoeId === doeId ? null : doeId
      }
    }
  }
}
</script>

<style scoped>
.project-list {
  padding: var(--spacing-lg);
  min-height: 100vh;
}

.page-title {
  font-size: var(--font-size-xl);
  font-weight: bold;
  color: var(--text-primary);
  margin-bottom: var(--spacing-lg);
}

.project-cards {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.project-card {
  background:
    linear-gradient(135deg, rgba(0, 212, 255, 0.08), rgba(7, 18, 38, 0.08)),
    var(--surface-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-md);
}

.project-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
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
  font-size: var(--font-size-xl);
  color: var(--text-primary);
}

.project-subtitle {
  margin: var(--spacing-xs) 0 0 0;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
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

.project-summary {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.summary-row {
  display: grid;
  grid-template-columns: 140px minmax(0, 1fr);
  gap: var(--spacing-md);
  align-items: start;
}

.summary-label,
.detail-label,
.factor-name {
  font-weight: var(--font-weight-semibold);
  color: var(--primary-color);
}

.summary-value,
.detail-value,
.factor-condition {
  color: var(--text-primary);
  line-height: 1.6;
}

.multiline {
  white-space: pre-wrap;
  word-break: break-word;
}

.doe-row {
  align-items: center;
}

.doe-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.doe-chip,
.collapse-button {
  border: 1px solid var(--border-primary);
  background: rgba(0, 212, 255, 0.08);
  color: var(--text-primary);
  border-radius: var(--radius-full);
  padding: 0.45rem 0.9rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.doe-chip:hover,
.collapse-button:hover,
.doe-chip.active {
  background: rgba(0, 212, 255, 0.2);
  color: var(--primary-color);
  transform: translateY(-1px);
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

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-md);
}

.detail-grid.compact {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.detail-card,
.factor-card {
  background: var(--surface-tertiary);
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

.factor-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-md);
}

.factor-card.changed {
  border-left: 3px solid #f59e0b;
}

.factor-card.result {
  border-left: 3px solid #22c55e;
}

.state-message {
  padding: var(--spacing-lg);
  border-radius: var(--radius-md);
  background: var(--surface-secondary);
  color: var(--text-secondary);
}

.state-message.error {
  color: var(--error-color);
  background: rgba(255, 0, 0, 0.08);
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

@media (max-width: 768px) {
  .project-list {
    padding: var(--spacing-md);
  }

  .project-card {
    padding: var(--spacing-md);
  }

  .project-card-header,
  .doe-panel-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .summary-row,
  .detail-grid,
  .detail-grid.compact,
  .factor-grid {
    grid-template-columns: 1fr;
  }

  .summary-row {
    gap: var(--spacing-xs);
  }
}
</style>
