<template>
  <div class="dashboard">
    <header class="dashboard-header">
      <h1>Project Dashboard</h1>
      <div class="header-actions">
        <button class="btn-primary" @click="showCreateForm = true">New Project</button>
      </div>
    </header>
    
    <main class="main">
      <!-- 数据大屏 -->
      <section class="dashboard-section">
        <h2>Project Overview</h2>
        <div class="stats-grid">
          <div class="stat-card">
            <h3>Total Projects</h3>
            <p>{{ projects.length }}</p>
          </div>
          <div class="stat-card">
            <h3>Active Projects</h3>
            <p>{{ activeProjects }}</p>
          </div>
          <div class="stat-card">
            <h3>Package Types</h3>
            <p>{{ uniquePackageTypes }}</p>
          </div>
          <div class="stat-card">
            <h3>New Technologies</h3>
            <p>{{ uniqueTechnologies }}</p>
          </div>
        </div>
      </section>
      
      <!-- 筛选控件 -->
      <section class="filter-section">
        <div class="filter-controls">
          <div class="filter-group">
            <label>Package Type</label>
            <select v-model="filters.packageType" @change="applyFilters">
              <option value="">All</option>
              <option v-for="type in packageTypes" :key="type" :value="type">{{ type }}</option>
            </select>
          </div>
          <div class="filter-group">
            <label>Status</label>
            <select v-model="filters.status" @change="applyFilters">
              <option value="">All</option>
              <option value="Active">Active</option>
              <option value="Completed">Completed</option>
              <option value="On Hold">On Hold</option>
              <option value="Cancelled">Cancelled</option>
            </select>
          </div>
          <button class="btn-secondary" @click="resetFilters">Reset</button>
        </div>
      </section>
      
      <!-- 项目卡片列表 -->
      <section class="projects-section">
        <h2>Projects</h2>
        <div class="projects-grid">
          <div 
            v-for="(project, index) in filteredProjects" 
            :key="index"
            class="project-card"
            @click="viewProject(index)"
          >
            <div class="card-header">
              <h3>{{ project['project name'] }}</h3>
              <span :class="['status-badge', project['project status'].toLowerCase()]">
                {{ project['project status'] }}
              </span>
            </div>
            <div class="card-body">
              <p><strong>Package Type:</strong> {{ project['package type'] }}</p>
              <p><strong>Purpose:</strong> {{ truncateText(project.purpose, 50) }}</p>
              <p><strong>New Technology:</strong> {{ project['new technology'] }}</p>
            </div>
            <div class="card-footer">
              <button class="btn-secondary" @click.stop="editStatus(index)">
                Update Status
              </button>
            </div>
          </div>
        </div>
      </section>
    </main>
    
    <!-- 详细信息模态框 -->
    <div v-if="selectedProject" class="modal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>{{ selectedProject['project name'] }}</h2>
          <button class="close-btn" @click="selectedProject = null">&times;</button>
        </div>
        <div class="modal-body">
          <div class="detail-grid">
            <div class="detail-item">
              <strong>Package Type:</strong>
              <span>{{ selectedProject['package type'] }}</span>
            </div>
            <div class="detail-item">
              <strong>Purpose:</strong>
              <span>{{ selectedProject.purpose }}</span>
            </div>
            <div class="detail-item">
              <strong>New Technology:</strong>
              <span>{{ selectedProject['new technology'] }}</span>
            </div>
            <div class="detail-item">
              <strong>DOE Factor:</strong>
              <span>{{ selectedProject['DOE factor'] }}</span>
            </div>
            <div class="detail-item">
              <strong>DOE Result:</strong>
              <span>{{ selectedProject['DOE result'] }}</span>
            </div>
            <div class="detail-item">
              <strong>Best Recipe Setting:</strong>
              <span>{{ selectedProject['best pecipe setting'] }}</span>
            </div>
            <div class="detail-item">
              <strong>Engineer Insight:</strong>
              <span>{{ selectedProject['engineer insight(lesson learned)'] }}</span>
            </div>
            <div class="detail-item">
              <strong>Project Status:</strong>
              <span :class="['status-badge', selectedProject['project status'].toLowerCase()]">
                {{ selectedProject['project status'] }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 新建项目表单 -->
    <div v-if="showCreateForm" class="modal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>Create New Project</h2>
          <button class="close-btn" @click="showCreateForm = false">&times;</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="createProject">
            <div class="form-group">
              <label>Project Name</label>
              <input v-model="newProject['project name']" required />
            </div>
            <div class="form-group">
              <label>Package Type</label>
              <input v-model="newProject['package type']" required />
            </div>
            <div class="form-group">
              <label>Purpose</label>
              <textarea v-model="newProject.purpose" required></textarea>
            </div>
            <div class="form-group">
              <label>New Technology</label>
              <input v-model="newProject['new technology']" required />
            </div>
            <div class="form-group">
              <label>DOE Factor</label>
              <input v-model="newProject['DOE factor']" required />
            </div>
            <div class="form-group">
              <label>DOE Result</label>
              <input v-model="newProject['DOE result']" required />
            </div>
            <div class="form-group">
              <label>Best Recipe Setting</label>
              <input v-model="newProject['best pecipe setting']" required />
            </div>
            <div class="form-group">
              <label>Engineer Insight</label>
              <textarea v-model="newProject['engineer insight(lesson learned)']" required></textarea>
            </div>
            <div class="form-actions">
              <button type="button" class="btn-secondary" @click="showCreateForm = false">Cancel</button>
              <button type="submit" class="btn-primary">Create</button>
            </div>
          </form>
        </div>
      </div>
    </div>
    
    <!-- 状态更新模态框 -->
    <div v-if="showStatusForm" class="modal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>Update Project Status</h2>
          <button class="close-btn" @click="showStatusForm = false">&times;</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="updateStatus">
            <div class="form-group">
              <label>Status</label>
              <select v-model="statusUpdate.status" required>
                <option value="Active">Active</option>
                <option value="Completed">Completed</option>
                <option value="On Hold">On Hold</option>
                <option value="Cancelled">Cancelled</option>
              </select>
            </div>
            <div class="form-actions">
              <button type="button" class="btn-secondary" @click="showStatusForm = false">Cancel</button>
              <button type="submit" class="btn-primary">Update</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Dashboard',
  data() {
    return {
      projects: [],
      selectedProject: null,
      showCreateForm: false,
      showStatusForm: false,
      newProject: {
        'project name': '',
        'package type': '',
        purpose: '',
        'new technology': '',
        'DOE factor': '',
        'DOE result': '',
        'best pecipe setting': '',
        'engineer insight(lesson learned)': ''
      },
      statusUpdate: {
        index: -1,
        status: 'Active'
      },
      filters: {
        packageType: '',
        status: ''
      }
    }
  },
  computed: {
    activeProjects() {
      return this.projects.filter(p => p['project status'] === 'Active').length
    },
    uniquePackageTypes() {
      const types = new Set(this.projects.map(p => p['package type']))
      return types.size
    },
    uniqueTechnologies() {
      const techs = new Set(this.projects.map(p => p['new technology']))
      return techs.size
    },
    packageTypes() {
      const types = new Set(this.projects.map(p => p['package type']))
      return Array.from(types).sort()
    },
    filteredProjects() {
      return this.projects.filter(project => {
        const matchesPackageType = !this.filters.packageType || 
          project['package type'] === this.filters.packageType
        const matchesStatus = !this.filters.status || 
          project['project status'] === this.filters.status
        return matchesPackageType && matchesStatus
      })
    }
  },
  mounted() {
    this.fetchProjects()
  },
  methods: {
    async fetchProjects() {
      try {
        const response = await fetch('http://localhost:5000/api/projects')
        this.projects = await response.json()
      } catch (error) {
        console.error('Error fetching projects:', error)
      }
    },
    async createProject() {
      try {
        const response = await fetch('http://localhost:5000/api/projects', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(this.newProject)
        })
        const newProject = await response.json()
        this.projects.push(newProject)
        this.showCreateForm = false
        this.resetForm()
      } catch (error) {
        console.error('Error creating project:', error)
      }
    },
    async updateStatus() {
      try {
        await fetch(`http://localhost:5000/api/projects/${this.statusUpdate.index}/status`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ status: this.statusUpdate.status })
        })
        this.projects[this.statusUpdate.index]['project status'] = this.statusUpdate.status
        this.showStatusForm = false
      } catch (error) {
        console.error('Error updating status:', error)
      }
    },
    viewProject(index) {
      this.selectedProject = this.projects[index]
    },
    editStatus(index) {
      this.statusUpdate.index = index
      this.statusUpdate.status = this.projects[index]['project status']
      this.showStatusForm = true
    },
    resetForm() {
      this.newProject = {
        'project name': '',
        'package type': '',
        purpose: '',
        'new technology': '',
        'DOE factor': '',
        'DOE result': '',
        'best pecipe setting': '',
        'engineer insight(lesson learned)': ''
      }
    },
    truncateText(text, length) {
      return text.length > length ? text.substring(0, length) + '...' : text
    },
    applyFilters() {
      // 筛选已在computed中处理
    },
    resetFilters() {
      this.filters = {
        packageType: '',
        status: ''
      }
    }
  }
}
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  color: #e0e0e0;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 40px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 100;
}

.dashboard-header h1 {
  margin: 0;
  font-size: 1.8rem;
  color: #00d4ff;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.main {
  padding: 40px;
}

.dashboard-section {
  margin-bottom: 40px;
}

.dashboard-section h2 {
  color: #00d4ff;
  margin-bottom: 20px;
  font-size: 1.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.05);
  padding: 20px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  text-align: center;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 212, 255, 0.2);
}

.stat-card h3 {
  margin: 0 0 10px 0;
  font-size: 1rem;
  color: #b0b0b0;
}

.stat-card p {
  margin: 0;
  font-size: 2rem;
  font-weight: bold;
  color: #00d4ff;
}

.filter-section {
  margin-bottom: 30px;
}

.filter-controls {
  display: flex;
  gap: 20px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.filter-group label {
  font-size: 0.9rem;
  color: #00d4ff;
}

.filter-group select {
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 5px;
  color: #ffffff;
  font-size: 0.9rem;
  min-width: 150px;
  font-weight: 500;
}

.filter-group select option {
  background-color: #2a2a4e;
  color: #ffffff;
  padding: 8px 12px;
}

.projects-section h2 {
  color: #00d4ff;
  margin-bottom: 20px;
  font-size: 1.5rem;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.project-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 20px;
  cursor: pointer;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.project-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 212, 255, 0.2);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.card-header h3 {
  margin: 0;
  font-size: 1.2rem;
  color: #00d4ff;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: bold;
}

.status-badge.active {
  background: rgba(0, 255, 128, 0.2);
  color: #00ff80;
  border: 1px solid rgba(0, 255, 128, 0.4);
}

.status-badge.completed {
  background: rgba(0, 191, 255, 0.2);
  color: #00bfff;
  border: 1px solid rgba(0, 191, 255, 0.4);
}

.status-badge.on-hold {
  background: rgba(255, 215, 0, 0.2);
  color: #ffd700;
  border: 1px solid rgba(255, 215, 0, 0.4);
}

.status-badge.cancelled {
  background: rgba(255, 69, 0, 0.2);
  color: #ff4500;
  border: 1px solid rgba(255, 69, 0, 0.4);
}

.card-body p {
  margin: 8px 0;
  font-size: 0.9rem;
  line-height: 1.4;
}

.card-footer {
  margin-top: 20px;
  text-align: right;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: #1a1a2e;
  border-radius: 10px;
  border: 1px solid rgba(0, 212, 255, 0.3);
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 0 30px rgba(0, 212, 255, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header h2 {
  margin: 0;
  color: #00d4ff;
}

.close-btn {
  background: none;
  border: none;
  color: #e0e0e0;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #00d4ff;
}

.modal-body {
  padding: 20px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 15px;
}

.detail-item {
  display: flex;
  flex-direction: column;
}

.detail-item strong {
  color: #00d4ff;
  margin-bottom: 5px;
  font-size: 0.9rem;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  color: #00d4ff;
  font-size: 0.9rem;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 10px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 5px;
  color: #e0e0e0;
  font-size: 0.9rem;
}

.form-group select {
  background-color: #2a2a4e;
  cursor: pointer;
}

.form-group select option {
  background-color: #ffffff;
  color: #1a1a2e;
  padding: 10px;
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.btn-primary {
  background: linear-gradient(135deg, #00d4ff, #0099cc);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: bold;
  transition: all 0.3s ease;
  text-decoration: none;
  display: inline-block;
  text-align: center;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 212, 255, 0.4);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: #e0e0e0;
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: #00d4ff;
}

@media (max-width: 768px) {
  .header {
    padding: 15px 20px;
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .header-actions {
    align-self: flex-end;
  }
  
  .header h1 {
    font-size: 1.4rem;
  }
  
  .main {
    padding: 20px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .filter-controls {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .projects-grid {
    grid-template-columns: 1fr;
  }
  
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
