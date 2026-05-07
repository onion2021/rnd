<template>
  <div class="doe-comparison-page">
    <header class="page-header">
      <div>
        <p class="page-kicker">Experiment Analysis</p>
        <h2 class="page-title">DOE Comparison</h2>
      </div>
      <p class="page-description">
        Select 2 to 4 DOE rows and compare tools, locations, objectives, factors, and learnings side by side.
      </p>
    </header>

    <div v-if="loading" class="state-message">Loading DOE data...</div>
    <div v-else-if="error" class="state-message error">{{ error }}</div>
    <div v-else>
      <section class="selector-panel">
        <div class="selector-header">
          <div>
            <h3>Select DOE</h3>
            <p>Search by project, DOE number, tool, location, or title.</p>
          </div>
          <span class="selection-count">{{ selectedDoes.length }}/4 selected</span>
        </div>

        <div class="selector-actions">
          <input
            v-model.trim="searchTerm"
            type="text"
            class="search-input"
            placeholder="Search DOE, project, tool, location..."
          />
          <button type="button" class="btn-secondary" @click="clearSelection">
            Clear Selection
          </button>
        </div>

        <p v-if="selectionWarning" class="selection-warning">{{ selectionWarning }}</p>

        <div class="doe-option-grid">
          <button
            v-for="option in filteredDoeOptions"
            :key="option.id"
            type="button"
            class="doe-option"
            :class="{ selected: isSelected(option.id) }"
            @click="toggleDoe(option.id)"
          >
            <span class="option-project">{{ option.projectDisplay }}</span>
            <strong>DOE {{ option.doe_number || 'N/A' }}</strong>
            <span class="option-title">{{ option.title || 'Untitled DOE' }}</span>
            <span class="option-meta">
              {{ option.tool || 'No tool' }} / {{ option.location || 'No location' }}
            </span>
          </button>
        </div>
      </section>

      <div v-if="selectedDoes.length < 2" class="state-message empty">
        Select at least 2 DOE rows to start the comparison.
      </div>

      <section v-else class="comparison-workspace">
        <div class="selected-strip">
          <article
            v-for="doe in selectedDoes"
            :key="doe.id"
            class="selected-card"
          >
            <div>
              <p class="selected-project">{{ doe.projectDisplay }}</p>
              <h3>DOE {{ doe.doe_number || 'N/A' }}</h3>
            </div>
            <button type="button" class="remove-button" @click="toggleDoe(doe.id)">
              Remove
            </button>
          </article>
        </div>

        <section class="comparison-section">
          <div class="section-heading">
            <h3>Snapshot</h3>
            <p>Core DOE context for quick screening.</p>
          </div>
          <div class="comparison-table-wrap">
            <table class="comparison-table">
              <thead>
                <tr>
                  <th>Field</th>
                  <th v-for="doe in selectedDoes" :key="doe.id">
                    DOE {{ doe.doe_number || 'N/A' }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="field in comparisonFields" :key="field.label">
                  <th>{{ field.label }}</th>
                  <td v-for="doe in selectedDoes" :key="`${doe.id}-${field.label}`">
                    <div class="cell-content">{{ getComparisonValue(doe, field) }}</div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="comparison-section">
          <div class="section-heading">
            <h3>Factor Matrix</h3>
            <p>Fixed and changed factors aligned by factor name.</p>
          </div>
          <div v-if="!factorRows.length" class="state-message empty">
            No fixed or changed factors available for the selected DOE rows.
          </div>
          <div v-else class="comparison-table-wrap">
            <table class="comparison-table">
              <thead>
                <tr>
                  <th>Factor</th>
                  <th v-for="doe in selectedDoes" :key="doe.id">
                    DOE {{ doe.doe_number || 'N/A' }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in factorRows" :key="row.name">
                  <th>
                    <span>{{ row.name }}</span>
                    <small>{{ row.type }}</small>
                  </th>
                  <td v-for="doe in selectedDoes" :key="`${doe.id}-${row.name}`">
                    <div class="cell-content">{{ getFactorValue(doe, row.name) }}</div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="insight-panel">
          <h3>Comparison Signals</h3>
          <div class="signal-grid">
            <div class="signal-card">
              <span>Tools</span>
              <strong>{{ uniqueTools.length }}</strong>
              <p>{{ uniqueTools.join(', ') || 'No tool data' }}</p>
            </div>
            <div class="signal-card">
              <span>Locations</span>
              <strong>{{ uniqueLocations.length }}</strong>
              <p>{{ uniqueLocations.join(', ') || 'No location data' }}</p>
            </div>
            <div class="signal-card">
              <span>Factor Names</span>
              <strong>{{ factorRows.length }}</strong>
              <p>Unique fixed or changed factor names across selected DOE rows.</p>
            </div>
          </div>
        </section>
      </section>
    </div>
  </div>
</template>

<script>
import { apiUrl } from '../api'

export default {
  name: 'DOEComparison',
  data() {
    return {
      projects: [],
      selectedDoeIds: [],
      searchTerm: '',
      selectionWarning: '',
      loading: true,
      error: null,
      comparisonFields: [
        { label: 'Project Name', source: 'project' },
        { label: 'Tool', labels: ['Tool'] },
        { label: 'Location', labels: ['Location'] },
        { label: 'Test Purpose', labels: ['Test purpose'] },
        { label: 'Background', labels: ['Background'] },
        { label: 'DOE Details', labels: ['DOE Details'] },
        { label: 'DOE Legs', labels: ['DOE Legs Listed', 'DOE Legs'] },
        { label: 'Result / Learnings', labels: ['Result / Learnings', 'Result', 'Summary', 'Overall Findings', 'Overall summary / Learnings', 'Evaluation Result'] }
      ]
    }
  },
  computed: {
    allDoeOptions() {
      return this.projects.flatMap(project => {
        const projectDisplay = project.display_name || project.name
        return this.getProjectDoes(project).map(doe => ({
          ...doe,
          projectId: project.id,
          projectName: project.name,
          projectDisplay,
          tool: this.getFieldValue(doe, ['Tool']),
          location: this.getFieldValue(doe, ['Location'])
        }))
      })
    },
    filteredDoeOptions() {
      const query = this.normalize(this.searchTerm)
      if (!query) return this.allDoeOptions

      return this.allDoeOptions.filter(doe => {
        const text = [
          doe.projectDisplay,
          doe.projectName,
          doe.doe_number,
          doe.activity_flow_doe_number,
          doe.title,
          doe.tool,
          doe.location
        ].join(' ')
        return this.normalize(text).includes(query)
      })
    },
    selectedDoes() {
      return this.selectedDoeIds
        .map(id => this.allDoeOptions.find(doe => doe.id === id))
        .filter(Boolean)
    },
    factorRows() {
      const rows = new Map()

      for (const doe of this.selectedDoes) {
        for (const factor of this.getAllFactors(doe)) {
          const name = String(factor.name || '').trim()
          if (!name) continue
          const key = this.normalize(name)
          const existing = rows.get(key)
          const type = factor.type || 'Factor'
          rows.set(key, {
            name,
            type: existing?.type && existing.type !== type ? 'Mixed' : type
          })
        }
      }

      return Array.from(rows.values()).sort((a, b) => a.name.localeCompare(b.name))
    },
    uniqueTools() {
      return this.uniqueValues(this.selectedDoes.map(doe => doe.tool))
    },
    uniqueLocations() {
      return this.uniqueValues(this.selectedDoes.map(doe => doe.location))
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
          throw new Error('Failed to fetch DOE data')
        }
        this.projects = await response.json()
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    normalize(value) {
      return String(value || '').replace(/\s+/g, ' ').trim().toLowerCase()
    },
    getProjectDoes(project) {
      return Array.isArray(project.does) ? project.does : []
    },
    isSelected(doeId) {
      return this.selectedDoeIds.includes(doeId)
    },
    toggleDoe(doeId) {
      this.selectionWarning = ''

      if (this.isSelected(doeId)) {
        this.selectedDoeIds = this.selectedDoeIds.filter(id => id !== doeId)
        return
      }

      if (this.selectedDoeIds.length >= 4) {
        this.selectionWarning = 'You can compare up to 4 DOE rows at once.'
        return
      }

      this.selectedDoeIds = [...this.selectedDoeIds, doeId]
    },
    clearSelection() {
      this.selectedDoeIds = []
      this.selectionWarning = ''
    },
    getFieldValue(doe, labels) {
      const normalizedLabels = labels.map(label => this.normalize(label))
      const field = (doe.detail_fields || []).find(item => {
        const label = this.normalize(item.label || item.key)
        return normalizedLabels.includes(label)
      })
      return field?.value || ''
    },
    getComparisonValue(doe, field) {
      if (field.source === 'project') return doe.projectDisplay || '-'
      return this.getFieldValue(doe, field.labels || []) || '-'
    },
    getAllFactors(doe) {
      const fixedFactors = (doe.fixed_factors || []).map(factor => ({
        ...factor,
        type: 'Fixed'
      }))
      const changedFactors = (doe.changed_factors || []).map(factor => ({
        ...factor,
        type: 'Changed'
      }))
      return [...fixedFactors, ...changedFactors]
    },
    getFactorValue(doe, factorName) {
      const target = this.normalize(factorName)
      const matches = this.getAllFactors(doe).filter(factor => this.normalize(factor.name) === target)
      if (!matches.length) return '-'
      return matches.map(factor => `${factor.type}: ${factor.condition || '-'}`).join('\n')
    },
    uniqueValues(values) {
      const seen = new Set()
      const output = []
      for (const value of values) {
        const clean = String(value || '').trim()
        const key = this.normalize(clean)
        if (!key || seen.has(key)) continue
        seen.add(key)
        output.push(clean)
      }
      return output
    }
  }
}
</script>

<style scoped>
.doe-comparison-page {
  padding: var(--spacing-lg);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.page-kicker {
  margin: 0 0 var(--spacing-xs) 0;
  color: var(--primary-color);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.page-title {
  margin: 0;
  color: var(--text-primary);
  font-size: var(--font-size-xl);
}

.page-description {
  max-width: 560px;
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
  text-align: right;
}

.selector-panel,
.comparison-section,
.insight-panel {
  background:
    linear-gradient(135deg, rgba(0, 212, 255, 0.08), rgba(7, 18, 38, 0.08)),
    var(--surface-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-md);
}

.selector-panel {
  margin-bottom: var(--spacing-lg);
}

.selector-header,
.selector-actions,
.section-heading,
.selected-strip,
.signal-grid {
  display: flex;
  gap: var(--spacing-md);
}

.selector-header,
.section-heading {
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-md);
}

.selector-header h3,
.section-heading h3,
.insight-panel h3 {
  margin: 0;
  color: var(--text-primary);
}

.selector-header p,
.section-heading p {
  margin: var(--spacing-xs) 0 0 0;
  color: var(--text-secondary);
}

.selection-count {
  flex-shrink: 0;
  padding: var(--spacing-xs) var(--spacing-sm);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-full);
  color: var(--primary-color);
  font-weight: var(--font-weight-semibold);
}

.selector-actions {
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.search-input {
  flex: 1;
  padding: var(--spacing-sm) var(--spacing-md);
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-primary);
}

.search-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
}

.selection-warning {
  margin: 0 0 var(--spacing-md) 0;
  color: #f59e0b;
}

.doe-option-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--spacing-md);
  max-height: 360px;
  overflow: auto;
  padding-right: var(--spacing-xs);
}

.doe-option {
  text-align: left;
  background: var(--surface-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  padding: var(--spacing-md);
  transition: all var(--transition-fast);
}

.doe-option:hover,
.doe-option.selected {
  border-color: var(--primary-color);
  background: rgba(0, 212, 255, 0.12);
  transform: translateY(-1px);
}

.option-project,
.option-meta {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}

.option-title {
  color: var(--text-primary);
  line-height: 1.5;
}

.comparison-workspace {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.selected-strip {
  flex-wrap: wrap;
}

.selected-card {
  min-width: 220px;
  flex: 1;
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
}

.selected-card h3,
.selected-project {
  margin: 0;
}

.selected-project {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}

.remove-button {
  align-self: flex-start;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  cursor: pointer;
  padding: var(--spacing-xs) var(--spacing-sm);
}

.remove-button:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.comparison-table-wrap {
  overflow-x: auto;
}

.comparison-table {
  width: 100%;
  min-width: 760px;
  border-collapse: collapse;
}

.comparison-table th,
.comparison-table td {
  vertical-align: top;
  border: 1px solid var(--border-color);
  padding: var(--spacing-md);
}

.comparison-table thead th {
  background: rgba(0, 212, 255, 0.14);
  color: var(--primary-color);
}

.comparison-table tbody th {
  width: 190px;
  background: var(--surface-primary);
  color: var(--primary-color);
  text-align: left;
}

.comparison-table tbody th small {
  display: block;
  margin-top: var(--spacing-xs);
  color: var(--text-tertiary);
  font-weight: var(--font-weight-normal);
}

.cell-content {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

.insight-panel h3 {
  margin-bottom: var(--spacing-md);
}

.signal-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.signal-card {
  background: var(--surface-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}

.signal-card span {
  color: var(--primary-color);
  font-weight: var(--font-weight-semibold);
}

.signal-card strong {
  display: block;
  margin: var(--spacing-sm) 0;
  font-size: var(--font-size-xxl);
}

.signal-card p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
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

.state-message.empty {
  border: 1px dashed var(--border-primary);
}

@media (max-width: 768px) {
  .doe-comparison-page {
    padding: var(--spacing-md);
  }

  .page-header,
  .selector-header,
  .selector-actions,
  .section-heading {
    align-items: stretch;
    flex-direction: column;
  }

  .page-description {
    max-width: none;
    text-align: left;
  }

  .signal-grid {
    grid-template-columns: 1fr;
  }
}
</style>
