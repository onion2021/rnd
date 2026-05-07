<template>
  <div class="doe-design-page">
    <header class="page-header">
      <div>
        <p class="page-kicker">Experiment Planning</p>
        <h2 class="page-title">DOE Design Assistant</h2>
      </div>
      <p class="page-description">
        Describe the target issue, define factors and levels, then generate a DOE matrix using full factorial,
        fractional factorial, or response surface design.
      </p>
    </header>

    <section class="planner-grid">
      <article class="panel problem-panel">
        <div class="panel-heading">
          <h3>1. Target Problem</h3>
          <p>Use packaging language such as blister, adhesion, void, warpage, delamination, or peel strength.</p>
        </div>
        <textarea
          v-model.trim="targetProblem"
          class="problem-input"
          placeholder="Example: Improve copper adhesion after dry desmear while avoiding blister risk..."
        ></textarea>
      </article>

      <article class="panel recommendation-panel">
        <div class="panel-heading">
          <h3>Recommended Factors</h3>
          <p>Rule-based first pass from the target problem. Add useful factors into the design table.</p>
        </div>
        <div class="recommendation-list">
          <button
            v-for="factor in recommendations.factors"
            :key="factor.name"
            type="button"
            class="recommendation-chip"
            @click="addRecommendedFactor(factor)"
          >
            <strong>{{ factor.name }}</strong>
            <span>{{ factor.levels.join(', ') }}</span>
          </button>
        </div>
      </article>
    </section>

    <section class="panel method-panel">
      <div class="panel-heading">
        <h3>2. DOE Method</h3>
        <p>Choose the design strategy. The assistant will generate the matrix from your factor levels.</p>
      </div>

      <div class="method-grid">
        <button
          v-for="method in methodCards"
          :key="method.id"
          type="button"
          class="method-card"
          :class="{ selected: selectedMethod === method.id }"
          @click="selectedMethod = method.id"
        >
          <span>{{ method.tag }}</span>
          <strong>{{ method.name }}</strong>
          <p>{{ method.description }}</p>
        </button>
      </div>
    </section>

    <section class="panel factor-panel">
      <div class="panel-heading">
        <h3>3. Factors and Levels</h3>
        <p>Separate levels with commas. Full factorial uses all levels; fractional factorial uses low/high; response surface uses low/center/high.</p>
      </div>

      <div class="factor-table-wrap">
        <table class="factor-table">
          <thead>
            <tr>
              <th>Factor</th>
              <th>Type</th>
              <th>Levels</th>
              <th>Unit / Note</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="factor in factors" :key="factor.id">
              <td>
                <input v-model.trim="factor.name" placeholder="Factor name" />
              </td>
              <td>
                <select v-model="factor.type">
                  <option value="continuous">Continuous</option>
                  <option value="categorical">Categorical</option>
                </select>
              </td>
              <td>
                <input v-model.trim="factor.levels" placeholder="Low, Center, High" />
              </td>
              <td>
                <input v-model.trim="factor.note" placeholder="C, W, sec, supplier..." />
              </td>
              <td>
                <button type="button" class="icon-button" @click="removeFactor(factor.id)">
                  Remove
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="factor-actions">
        <button type="button" class="btn-secondary" @click="addFactor">Add Factor</button>
        <button type="button" class="btn-secondary" @click="loadExample">Load Example</button>
        <button type="button" class="btn-primary" @click="generateDesign">Generate DOE Table</button>
      </div>

      <p v-if="validationMessage" class="validation-message">{{ validationMessage }}</p>
    </section>

    <section class="result-layout">
      <article class="panel risk-panel">
        <div class="panel-heading">
          <h3>Risk Points</h3>
          <p>Review before committing experiments to lab or supplier runs.</p>
        </div>
        <ul class="risk-list">
          <li v-for="risk in combinedRisks" :key="risk">{{ risk }}</li>
        </ul>
      </article>

      <article class="panel matrix-panel">
        <div class="panel-heading">
          <div>
            <h3>Generated DOE Table</h3>
            <p>{{ matrixSummary }}</p>
          </div>
          <button
            v-if="generatedRows.length"
            type="button"
            class="btn-secondary"
            @click="copyMatrix"
          >
            Copy CSV
          </button>
        </div>

        <div v-if="!generatedRows.length" class="state-message empty">
          No DOE table generated yet. Fill in factors, choose a method, then click Generate DOE Table.
        </div>

        <div v-else class="matrix-table-wrap">
          <table class="matrix-table">
            <thead>
              <tr>
                <th>Run</th>
                <th v-for="factor in activeFactors" :key="factor.id">{{ factor.name }}</th>
                <th>Design Note</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in generatedRows" :key="row.run">
                <td>{{ row.run }}</td>
                <td v-for="factor in activeFactors" :key="`${row.run}-${factor.id}`">
                  {{ row.values[factor.name] || '-' }}
                </td>
                <td>{{ row.note }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>
    </section>
  </div>
</template>

<script>
export default {
  name: 'DOEDesignAssistant',
  data() {
    return {
      targetProblem: '',
      selectedMethod: 'full-factorial',
      nextFactorId: 4,
      generatedRows: [],
      validationMessage: '',
      factors: [
        { id: 1, name: 'Tool', type: 'categorical', levels: 'CHQ2, Supplier Tool', note: 'tool source' },
        { id: 2, name: 'Plasma Power', type: 'continuous', levels: 'Low, Center, High', note: 'W' },
        { id: 3, name: 'Treatment Time', type: 'continuous', levels: 'Short, Nominal, Long', note: 'sec' }
      ],
      methodCards: [
        {
          id: 'full-factorial',
          tag: 'Full',
          name: 'Full Factorial Design',
          description: 'Tests every level combination. Best when factor count is small and interaction coverage matters.'
        },
        {
          id: 'fractional-factorial',
          tag: 'Screen',
          name: 'Fractional Factorial Design',
          description: 'Uses low/high levels to screen many factors with fewer runs. Best for early pathfinding.'
        },
        {
          id: 'response-surface',
          tag: 'RSM',
          name: 'Response Surface Design',
          description: 'Uses low/center/high points to estimate curvature and optimize process windows.'
        }
      ]
    }
  },
  computed: {
    activeFactors() {
      return this.factors
        .map(factor => ({
          ...factor,
          name: String(factor.name || '').trim(),
          parsedLevels: this.parseLevels(factor.levels)
        }))
        .filter(factor => factor.name)
    },
    recommendations() {
      return this.buildRecommendations(this.targetProblem)
    },
    combinedRisks() {
      const methodRiskMap = {
        'full-factorial': 'Full factorial run count grows quickly; confirm sample availability before release.',
        'fractional-factorial': 'Fractional factorial can alias interactions; confirm critical interactions in follow-up DOE.',
        'response-surface': 'Response surface design assumes mostly continuous factors and stable measurement response.'
      }
      return [...this.recommendations.risks, methodRiskMap[this.selectedMethod]]
    },
    matrixSummary() {
      if (!this.generatedRows.length) return 'Waiting for design generation.'
      return `${this.generatedRows.length} runs generated with ${this.activeFactors.length} factor(s).`
    }
  },
  methods: {
    parseLevels(value) {
      return String(value || '')
        .split(/[,;|\n]+/)
        .map(level => level.trim())
        .filter(Boolean)
    },
    addFactor() {
      this.factors.push({
        id: this.nextFactorId,
        name: '',
        type: 'continuous',
        levels: 'Low, Center, High',
        note: ''
      })
      this.nextFactorId += 1
    },
    addRecommendedFactor(factor) {
      const exists = this.activeFactors.some(item => item.name.toLowerCase() === factor.name.toLowerCase())
      if (exists) {
        this.validationMessage = `${factor.name} is already in the factor list.`
        return
      }

      this.factors.push({
        id: this.nextFactorId,
        name: factor.name,
        type: factor.type,
        levels: factor.levels.join(', '),
        note: factor.note || ''
      })
      this.nextFactorId += 1
      this.validationMessage = ''
    },
    removeFactor(id) {
      if (this.factors.length <= 1) {
        this.validationMessage = 'Keep at least one factor in the design.'
        return
      }
      this.factors = this.factors.filter(factor => factor.id !== id)
    },
    loadExample() {
      this.targetProblem = 'Improve copper adhesion after dry desmear and reduce blister risk.'
      this.factors = [
        { id: 1, name: 'Tool', type: 'categorical', levels: 'CHQ2, Supplier Tool', note: 'tool source' },
        { id: 2, name: 'Plasma Power', type: 'continuous', levels: 'Low, Center, High', note: 'W' },
        { id: 3, name: 'Treatment Time', type: 'continuous', levels: 'Short, Nominal, Long', note: 'sec' },
        { id: 4, name: 'Gas Chemistry', type: 'categorical', levels: 'CF4, CF4/O2, O2', note: 'plasma gas' }
      ]
      this.nextFactorId = 5
      this.generatedRows = []
      this.validationMessage = ''
    },
    validateDesign() {
      if (!this.activeFactors.length) return 'Please provide at least one factor.'

      const missingLevels = this.activeFactors.find(factor => factor.parsedLevels.length < 2)
      if (missingLevels) return `${missingLevels.name} needs at least two levels.`

      if (this.selectedMethod === 'response-surface') {
        const tooFewLevels = this.activeFactors.find(factor => factor.parsedLevels.length < 3)
        if (tooFewLevels) return `${tooFewLevels.name} needs low, center, and high levels for response surface design.`
      }

      return ''
    },
    generateDesign() {
      this.validationMessage = this.validateDesign()
      if (this.validationMessage) {
        this.generatedRows = []
        return
      }

      if (this.selectedMethod === 'full-factorial') {
        this.generatedRows = this.generateFullFactorial()
      } else if (this.selectedMethod === 'fractional-factorial') {
        this.generatedRows = this.generateFractionalFactorial()
      } else {
        this.generatedRows = this.generateResponseSurface()
      }
    },
    generateFullFactorial() {
      const runSets = this.activeFactors.reduce((rows, factor) => {
        const nextRows = []
        for (const row of rows) {
          for (const level of factor.parsedLevels) {
            nextRows.push({
              ...row,
              [factor.name]: level
            })
          }
        }
        return nextRows
      }, [{}])

      if (runSets.length > 256) {
        this.validationMessage = `Full factorial would create ${runSets.length} runs. Reduce factors/levels or use fractional factorial.`
        return []
      }

      return runSets.map((values, index) => ({
        run: index + 1,
        values,
        note: 'Full factorial combination'
      }))
    },
    generateFractionalFactorial() {
      const factors = this.activeFactors
      const runCount = Math.min(32, Math.pow(2, Math.ceil(Math.log2(factors.length + 1))))
      const baseColumns = Math.log2(runCount)
      const signRows = Array.from({ length: runCount }, (_, rowIndex) => {
        return Array.from({ length: baseColumns }, (_, columnIndex) => {
          return Math.floor(rowIndex / Math.pow(2, columnIndex)) % 2 === 0 ? -1 : 1
        })
      })

      return signRows.map((signs, rowIndex) => {
        const values = {}
        factors.forEach((factor, factorIndex) => {
          const low = factor.parsedLevels[0]
          const high = factor.parsedLevels[factor.parsedLevels.length - 1]
          let sign = signs[factorIndex]

          if (sign === undefined) {
            const first = signs[factorIndex % baseColumns]
            const second = signs[(factorIndex + 1) % baseColumns]
            sign = first * second
          }

          values[factor.name] = sign < 0 ? low : high
        })

        return {
          run: rowIndex + 1,
          values,
          note: 'Fractional factorial screening run'
        }
      })
    },
    generateResponseSurface() {
      const factors = this.activeFactors
      if (factors.length > 5) {
        this.validationMessage = 'Response surface design is limited to 5 factors in this assistant. Reduce factors or use screening first.'
        return []
      }

      const lowHighRows = factors.reduce((rows, factor) => {
        const low = factor.parsedLevels[0]
        const high = factor.parsedLevels[factor.parsedLevels.length - 1]
        const nextRows = []
        for (const row of rows) {
          nextRows.push({ ...row, [factor.name]: low })
          nextRows.push({ ...row, [factor.name]: high })
        }
        return nextRows
      }, [{}])

      const centerValues = {}
      factors.forEach(factor => {
        centerValues[factor.name] = factor.parsedLevels[Math.floor(factor.parsedLevels.length / 2)]
      })

      const axialRows = []
      factors.forEach(factor => {
        const low = factor.parsedLevels[0]
        const high = factor.parsedLevels[factor.parsedLevels.length - 1]
        axialRows.push({
          ...centerValues,
          [factor.name]: low
        })
        axialRows.push({
          ...centerValues,
          [factor.name]: high
        })
      })

      const centerRows = Array.from({ length: 3 }, () => ({ ...centerValues }))
      return [...lowHighRows, ...axialRows, ...centerRows].map((values, index) => ({
        run: index + 1,
        values,
        note: index >= lowHighRows.length + axialRows.length ? 'Center replicate' : 'Response surface point'
      }))
    },
    buildRecommendations(problem) {
      const normalized = String(problem || '').toLowerCase()
      const library = [
        {
          keywords: ['blister', 'bubble'],
          factors: [
            { name: 'Pre-bake Condition', type: 'continuous', levels: ['Low', 'Nominal', 'High'], note: 'temp/time' },
            { name: 'Plasma Power', type: 'continuous', levels: ['Low', 'Center', 'High'], note: 'W' },
            { name: 'Treatment Time', type: 'continuous', levels: ['Short', 'Nominal', 'Long'], note: 'sec' },
            { name: 'Moisture Exposure Time', type: 'continuous', levels: ['Short', 'Nominal', 'Long'], note: 'queue time' }
          ],
          risks: [
            'Blister experiments are sensitive to moisture history and queue time before lamination.',
            'Aggressive plasma can improve activation but may over-etch or create weak interfaces.'
          ]
        },
        {
          keywords: ['adhesion', 'peel', 'copper'],
          factors: [
            { name: 'Gas Chemistry', type: 'categorical', levels: ['CF4', 'CF4/O2', 'O2'], note: 'plasma gas' },
            { name: 'Plasma Power', type: 'continuous', levels: ['Low', 'Center', 'High'], note: 'W' },
            { name: 'Cu Surface Roughness', type: 'continuous', levels: ['Low', 'Target', 'High'], note: 'roughness' },
            { name: 'Post-treatment Bake', type: 'continuous', levels: ['Low', 'Nominal', 'High'], note: 'temp/time' }
          ],
          risks: [
            'Peel strength may trade off with copper attack or excessive roughening.',
            'Surface aging after treatment can mask the true process effect.'
          ]
        },
        {
          keywords: ['void', 'outgas'],
          factors: [
            { name: 'Vacuum Level', type: 'continuous', levels: ['Low', 'Nominal', 'High'], note: 'vacuum' },
            { name: 'Dispense Speed', type: 'continuous', levels: ['Slow', 'Nominal', 'Fast'], note: 'process speed' },
            { name: 'Cure Profile', type: 'categorical', levels: ['Profile A', 'Profile B', 'Profile C'], note: 'thermal profile' }
          ],
          risks: [
            'Void response is often sensitive to material age, viscosity, and environmental exposure.',
            'Inspect both void rate and void size distribution, not pass/fail only.'
          ]
        },
        {
          keywords: ['warpage', 'stress'],
          factors: [
            { name: 'Cure Temperature', type: 'continuous', levels: ['Low', 'Center', 'High'], note: 'C' },
            { name: 'Ramp Rate', type: 'continuous', levels: ['Slow', 'Nominal', 'Fast'], note: 'C/min' },
            { name: 'Material Lot', type: 'categorical', levels: ['Lot A', 'Lot B'], note: 'material' }
          ],
          risks: [
            'Warpage needs consistent measurement temperature and fixture conditions.',
            'Material lot and die/package geometry can dominate process-factor effects.'
          ]
        }
      ]

      const fallback = {
        factors: [
          { name: 'Tool', type: 'categorical', levels: ['Tool A', 'Tool B'], note: 'equipment' },
          { name: 'Process Time', type: 'continuous', levels: ['Low', 'Center', 'High'], note: 'sec/min' },
          { name: 'Temperature', type: 'continuous', levels: ['Low', 'Center', 'High'], note: 'C' },
          { name: 'Pressure', type: 'continuous', levels: ['Low', 'Center', 'High'], note: 'process pressure' }
        ],
        risks: [
          'Define one primary response and one or two guard-band responses before running the DOE.',
          'Keep material lot, operator, and measurement method controlled where possible.'
        ]
      }

      const matched = library.find(item => item.keywords.some(keyword => normalized.includes(keyword)))
      return matched || fallback
    },
    copyMatrix() {
      if (!this.generatedRows.length) return

      const headers = ['Run', ...this.activeFactors.map(factor => factor.name), 'Design Note']
      const rows = this.generatedRows.map(row => [
        row.run,
        ...this.activeFactors.map(factor => row.values[factor.name] || ''),
        row.note
      ])
      const csv = [headers, ...rows]
        .map(row => row.map(value => `"${String(value).replace(/"/g, '""')}"`).join(','))
        .join('\n')

      navigator.clipboard?.writeText(csv)
      this.validationMessage = 'DOE table copied as CSV.'
    }
  }
}
</script>

<style scoped>
.doe-design-page {
  padding: var(--spacing-lg);
  min-height: 100vh;
}

.page-header,
.planner-grid,
.result-layout,
.factor-actions,
.panel-heading,
.method-grid {
  display: flex;
  gap: var(--spacing-lg);
}

.page-header {
  justify-content: space-between;
  align-items: flex-end;
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
  max-width: 620px;
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
  text-align: right;
}

.planner-grid {
  align-items: stretch;
  margin-bottom: var(--spacing-lg);
}

.problem-panel {
  flex: 1.2;
}

.recommendation-panel {
  flex: 1;
}

.panel {
  background:
    linear-gradient(135deg, rgba(0, 212, 255, 0.08), rgba(7, 18, 38, 0.08)),
    var(--surface-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  padding: var(--spacing-lg);
}

.panel-heading {
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-md);
}

.panel-heading h3 {
  margin: 0;
  color: var(--text-primary);
}

.panel-heading p {
  margin: var(--spacing-xs) 0 0 0;
  color: var(--text-secondary);
  line-height: 1.5;
}

.problem-input {
  width: 100%;
  min-height: 150px;
  resize: vertical;
  padding: var(--spacing-md);
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
}

.problem-input:focus,
.factor-table input:focus,
.factor-table select:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
}

.recommendation-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-sm);
}

.recommendation-chip {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  text-align: left;
  color: var(--text-primary);
  background: var(--surface-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  padding: var(--spacing-md);
}

.recommendation-chip:hover {
  border-color: var(--primary-color);
  background: rgba(0, 212, 255, 0.1);
}

.recommendation-chip span {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}

.method-panel,
.factor-panel {
  margin-bottom: var(--spacing-lg);
}

.method-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.method-card {
  text-align: left;
  color: var(--text-primary);
  background: var(--surface-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  padding: var(--spacing-md);
  transition: all var(--transition-fast);
}

.method-card:hover,
.method-card.selected {
  border-color: var(--primary-color);
  background: rgba(0, 212, 255, 0.12);
  transform: translateY(-1px);
}

.method-card span {
  color: var(--primary-color);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.method-card strong {
  display: block;
  margin: var(--spacing-sm) 0;
}

.method-card p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.5;
}

.factor-table-wrap,
.matrix-table-wrap {
  overflow-x: auto;
}

.factor-table,
.matrix-table {
  width: 100%;
  border-collapse: collapse;
}

.factor-table th,
.factor-table td,
.matrix-table th,
.matrix-table td {
  border: 1px solid var(--border-color);
  padding: var(--spacing-sm);
  vertical-align: top;
}

.factor-table th,
.matrix-table th {
  background: rgba(0, 212, 255, 0.12);
  color: var(--primary-color);
  text-align: left;
}

.factor-table input,
.factor-table select {
  width: 100%;
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: var(--spacing-sm);
}

.factor-table select option {
  background: white;
  color: #1a1a2e;
}

.icon-button {
  color: var(--text-secondary);
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  cursor: pointer;
  padding: var(--spacing-xs) var(--spacing-sm);
}

.icon-button:hover {
  color: var(--primary-color);
  border-color: var(--primary-color);
}

.factor-actions {
  justify-content: flex-end;
  margin-top: var(--spacing-md);
}

.validation-message {
  margin: var(--spacing-md) 0 0 0;
  color: #f59e0b;
}

.result-layout {
  align-items: flex-start;
}

.risk-panel {
  flex: 0 0 320px;
}

.matrix-panel {
  flex: 1;
  min-width: 0;
}

.risk-list {
  margin: 0;
  padding-left: var(--spacing-lg);
  color: var(--text-secondary);
  line-height: 1.6;
}

.matrix-table {
  min-width: 760px;
}

.matrix-table td {
  color: var(--text-primary);
  line-height: 1.5;
}

.state-message {
  padding: var(--spacing-lg);
  border-radius: var(--radius-md);
  background: var(--surface-secondary);
  color: var(--text-secondary);
}

.state-message.empty {
  border: 1px dashed var(--border-primary);
}

@media (max-width: 900px) {
  .page-header,
  .planner-grid,
  .result-layout,
  .factor-actions,
  .panel-heading {
    flex-direction: column;
  }

  .page-description {
    max-width: none;
    text-align: left;
  }

  .method-grid,
  .recommendation-list {
    grid-template-columns: 1fr;
  }

  .risk-panel {
    flex-basis: auto;
    width: 100%;
  }
}
</style>
