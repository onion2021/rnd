<template>
  <div class="app">
    <aside class="sidebar">
      <div class="sidebar-brand">
        <h1>R&D AI Assistant</h1>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/ai-assistant" class="nav-item" active-class="active">
          <span class="nav-icon">🤖</span>
          <span>AI Assistant</span>
        </router-link>
        <router-link to="/flow-list" class="nav-item" active-class="active">
          <span class="nav-icon">📋</span>
          <span>Flow List</span>
        </router-link>
      </nav>
    </aside>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: row;
  width: 100%;
}

/* 侧边栏样式 */
.sidebar {
  width: var(--sidebar-width);
  background: var(--surface-secondary);
  backdrop-filter: blur(10px);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  z-index: 100;
  flex-shrink: 0;
  transition: all var(--transition-normal);
  animation: slideInLeft 0.5s ease-out;
}

@keyframes slideInLeft {
  from {
    transform: translateX(-100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.sidebar-brand {
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
  text-align: center;
}

.sidebar-brand h1 {
  margin: 0;
  font-size: var(--font-size-lg);
  color: var(--primary-color);
  font-weight: var(--font-weight-bold);
  line-height: var(--line-height-tight);
}

.sidebar-nav {
  flex: 1;
  padding: var(--spacing-md) 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.nav-item {
  color: var(--text-primary);
  text-decoration: none;
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: 0 var(--radius-xxl) var(--radius-xxl) 0;
  transition: all var(--transition-normal);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin: 0 var(--spacing-sm);
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  position: relative;
  overflow: hidden;
}

.nav-icon {
  font-size: var(--font-size-lg);
  width: 24px;
  text-align: center;
}

.nav-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 4px;
  height: 100%;
  background: var(--primary-color);
  transform: scaleY(0);
  transition: transform var(--transition-normal);
}

.nav-item:hover {
  background: rgba(0, 212, 255, 0.15);
  color: var(--primary-color);
  transform: translateX(8px);
  box-shadow: var(--shadow-lg);
}

.nav-item:hover::before {
  transform: scaleY(1);
}

.nav-item.active {
  background: rgba(0, 212, 255, 0.25);
  color: var(--primary-color);
  border: 1px solid var(--border-primary);
  transform: translateX(8px);
  box-shadow: var(--shadow-xl);
}

.nav-item.active::before {
  transform: scaleY(1);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  width: calc(100% - var(--sidebar-width));
  animation: fadeIn 0.6s ease-out;
}

/* 全局按钮样式 */
.btn-primary {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  color: white;
  border: none;
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-bold);
  transition: all var(--transition-normal);
  text-decoration: none;
  display: inline-block;
  text-align: center;
  white-space: nowrap;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-xl);
}

.btn-secondary {
  background: var(--surface-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--font-size-sm);
  transition: all var(--transition-normal);
  text-decoration: none;
  display: inline-block;
  text-align: center;
  white-space: nowrap;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
}

/* 模态框样式 */
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
  backdrop-filter: blur(5px);
}

.modal-content {
  background: var(--background-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: var(--shadow-xl);
  animation: modalFadeIn 0.3s ease;
}

@keyframes modalFadeIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
}

.modal-header h2 {
  margin: 0;
  color: var(--primary-color);
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: var(--font-size-xxl);
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  transition: all var(--transition-fast);
}

.close-btn:hover {
  color: var(--primary-color);
  background: rgba(0, 212, 255, 0.1);
}

.modal-body {
  padding: var(--spacing-lg);
}

/* 表单样式 */
.form-group {
  margin-bottom: var(--spacing-md);
}

.form-group label {
  display: block;
  margin-bottom: var(--spacing-xs);
  color: var(--primary-color);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: var(--spacing-sm);
  background: var(--surface-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  transition: all var(--transition-fast);
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
}

.form-group select {
  background-color: var(--background-tertiary);
  cursor: pointer;
}

.form-group select option {
  background-color: white;
  color: var(--background-primary);
  padding: var(--spacing-sm);
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-lg);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--border-color);
    animation: slideInTop 0.5s ease-out;
  }
  
  @keyframes slideInTop {
    from {
      transform: translateY(-100%);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }
  
  .sidebar-nav {
    flex-direction: row;
    padding: var(--spacing-sm);
    justify-content: center;
    gap: var(--spacing-xs);
  }
  
  .nav-item {
    margin: 0;
    border-radius: var(--radius-xxl);
    padding: var(--spacing-xs) var(--spacing-sm);
    font-size: var(--font-size-xs);
    gap: var(--spacing-xs);
  }
  
  .nav-icon {
    font-size: var(--font-size-sm);
    width: 20px;
  }
  
  .nav-item:hover,
  .nav-item.active {
    transform: none;
  }
  
  .sidebar-brand h1 {
    font-size: var(--font-size-md);
  }
  
  .main-content {
    width: 100%;
  }
  
  .btn-primary,
  .btn-secondary {
    padding: var(--spacing-xs) var(--spacing-sm);
    font-size: var(--font-size-xs);
  }
  
  .modal-content {
    width: 95%;
    max-width: 95%;
  }
}

/* 平板设备响应式设计 */
@media (min-width: 769px) and (max-width: 1024px) {
  .sidebar {
    width: 200px;
  }
  
  .main-content {
    width: calc(100% - 200px);
  }
  
  .sidebar-brand h1 {
    font-size: var(--font-size-md);
  }
  
  .nav-item {
    font-size: var(--font-size-sm);
    padding: var(--spacing-sm) var(--spacing-md);
  }
}
</style>