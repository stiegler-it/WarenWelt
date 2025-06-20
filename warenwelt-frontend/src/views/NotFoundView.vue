<template>
  <div class="not-found-container">
    <h1>404 - Seite nicht gefunden</h1>
    <p>Die von Ihnen angeforderte Seite konnte nicht gefunden werden.</p>
    <router-link to="/dashboard">Zurück zum Dashboard</router-link>
  </div>
</template>

<script setup>
// No specific script needed for this simple page
</script>

<style scoped>
.not-found-container {
  text-align: center;
  margin-top: 50px;
}
h1 {
  font-size: 2.5rem;
  color: #dc3545; /* A Bootstrap 'danger' like color */
}
p {
  font-size: 1.2rem;
  margin-bottom: 20px;
}
a {
  color: #007bff;
  text-decoration: none;
}
a:hover {
  text-decoration: underline;
}
</style>
