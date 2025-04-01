<script setup>
import { ref, computed, watch, nextTick } from 'vue';
import { searchOperators } from '../services/api';


// --- Reactive State Variables ---
const searchQuery = ref('');
const searchResults = ref([]);
const totalCount = ref(0);
const isLoading = ref(false);
const error = ref(null);
const currentPage = ref(0);
const limit = ref(20);
const showNoResults = ref(false);
const searchInput = ref(null);

// --- Computed Properties ---
const canLoadMore = computed(() => {
  const loadedCount = searchResults.value.length;
  return loadedCount < totalCount.value;
});

const resultsMessage = computed(() => {
  if (searchResults.value.length === 0) return '';
  return `${searchResults.value.length} de ${totalCount.value}`;
});

// --- Methods ---
async function performSearch(isNewSearch = true) {
  if (!searchQuery.value.trim()) {
    // Don't search if query is empty
    searchResults.value = [];
    totalCount.value = 0;
    currentPage.value = 0;
    error.value = null;
    showNoResults.value = false;
    return;
  }

  // Reset state for a new search
  if (isNewSearch) {
    currentPage.value = 0;
    searchResults.value = []; // Clear previous results for a new search
    totalCount.value = 0;
    showNoResults.value = false;
  }

  isLoading.value = true;
  error.value = null;
  const offset = currentPage.value * limit.value;

  try {
    // Simulate a minimum loading time for better UX
    const data = await searchOperators(searchQuery.value, limit.value, offset);
    
    // Append results if loading more, replace if it's a new search
    if (isNewSearch) {
      searchResults.value = data.results;
    } else {
      searchResults.value = [...searchResults.value, ...data.results];
    }
    
    totalCount.value = data.total_count;
    
    // Show no results message if needed
    await nextTick();
    showNoResults.value = isNewSearch && data.results.length === 0;
  } catch (err) {
    console.error("Search failed:", err);
    error.value = err.message || 'Falha ao buscar resultados.';
  } finally {
    isLoading.value = false;
  }
}

// Function to load the next page
function loadMore() {
  if (canLoadMore.value && !isLoading.value) {
    currentPage.value++; // Increment page
    performSearch(false); // Perform search, appending results
  }
}

// Focus the search input on mount
function focusSearchInput() {
  if (searchInput.value) {
    searchInput.value.focus();
  }
}

// Watch for changes in the search query with debounce
let debounceTimeout = null;
watch(searchQuery, (newValue) => {
  if (newValue.trim() === '') {
    searchResults.value = [];
    totalCount.value = 0;
    showNoResults.value = false;
    return;
  }
  
  clearTimeout(debounceTimeout);
  debounceTimeout = setTimeout(() => {
    performSearch(true);
  }, 500); // 500ms debounce
});

// Lifecycle hook equivalent
setTimeout(focusSearchInput, 100);
</script>

<template>
  <div class="search-container max-w-4xl mx-auto p-6 sm:p-8 rounded-xl shadow-lg bg-white my-8 font-sans">
    <h1 class="text-3xl font-bold mb-6 text-center text-primary">
      <span class="inline-block transform hover:scale-105 transition-transform duration-300">
        Busca de Operadoras
      </span>
    </h1>
    
    <!-- Search Input and Button -->
    <div class="search-form flex flex-col sm:flex-row gap-3 mb-8">
      <div class="relative flex-grow">
        <input
          ref="searchInput"
          type="text"
          v-model="searchQuery"
          placeholder="Digite nome, CNPJ, cidade..."
          @keyup.enter="performSearch(true)"
          :disabled="isLoading"
          class="w-full p-3 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-300 bg-gray-50"
        />
        <span class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </span>
      </div>
      <button
        @click="performSearch(true)"
        :disabled="isLoading"
        class="px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105 flex items-center justify-center"
      >
        <span v-if="isLoading" class="inline-block animate-spin mr-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </span>
        <span>{{ isLoading ? 'Buscando...' : 'Buscar' }}</span>
      </button>
    </div>
    
    <!-- Loading Skeletons -->
    <div v-if="isLoading && searchResults.length === 0" class="space-y-4">
      <div v-for="i in 3" :key="i" class="animate-pulse">
        <div class="h-24 bg-gray-200 rounded-lg mb-4"></div>
      </div>
    </div>
    
    <!-- Error Message Display -->
    <div v-if="error" 
         class="error-message my-5 p-4 text-red-700 bg-red-50 border-l-4 border-red-500 rounded-md text-center animate-fadeIn">
      <div class="flex items-center">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>{{ error }}</span>
      </div>
    </div>
    
    <!-- No Results Message -->
    <div v-if="showNoResults" class="text-center my-8 p-6 bg-gray-50 rounded-lg border border-gray-200 animate-fadeIn">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p class="text-lg text-gray-600">Nenhum resultado encontrado para "{{ searchQuery }}".</p>
      <p class="text-sm text-gray-500 mt-2">Tente usar termos mais gerais ou verifique a ortografia.</p>
    </div>
    
    <!-- Search Results -->
    <div v-if="searchResults.length > 0" class="results-container mt-6 animate-fadeIn">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-xl font-semibold text-gray-800">Resultados</h2>
        <span class="text-sm bg-primary-light text-primary px-3 py-1 rounded-full">{{ resultsMessage }}</span>
      </div>
      
      <!-- Results List with Transition -->
      <TransitionGroup 
        name="list" 
        tag="ul" 
        class="results-list space-y-4"
      >
        <li 
          v-for="operator in searchResults" 
          :key="operator.registro_ans" 
          class="result-item border border-gray-200 p-5 rounded-lg shadow-sm hover:shadow-md transition-all duration-300 bg-white"
        >
          <div class="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-2">
            <div class="flex-1">
              <h3 class="text-lg font-bold text-gray-800">{{ operator.razao_social }}</h3>
              <div class="inline-block bg-gray-100 text-gray-600 px-2 py-1 rounded text-sm mt-1">
                Registro ANS: {{ operator.registro_ans }}
              </div>
            </div>
            <div class="flex flex-col items-start sm:items-end gap-2">
              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-light text-primary">
                {{ operator.modalidade || 'Sem modalidade' }}
              </span>
              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                {{ operator.uf || 'N/A' }}
              </span>
            </div>
          </div>
          
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4 text-sm text-gray-600">
            <div class="flex items-start">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              <span>{{ operator.nome_fantasia || 'Nome fantasia não informado' }}</span>
            </div>
            <div class="flex items-start">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>CNPJ: {{ operator.cnpj || 'Não informado' }}</span>
            </div>
            <div class="flex items-start">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span>{{ operator.cidade || 'Cidade não informada' }}, {{ operator.uf || 'UF não informada' }}</span>
            </div>
          </div>
        </li>
      </TransitionGroup>
      
      <!-- Load More Button -->
      <div v-if="canLoadMore" class="load-more text-center mt-8">
        <button
          @click="loadMore"
          :disabled="isLoading"
          class="px-6 py-3 bg-secondary text-white rounded-lg hover:bg-secondary-dark focus:outline-none focus:ring-2 focus:ring-secondary focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105"
        >
          <span v-if="isLoading" class="inline-block animate-spin mr-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </span>
          {{ isLoading ? 'Carregando...' : 'Carregar Mais' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style>
:root {
  --color-primary: #2563eb;
  --color-primary-dark: #1d4ed8;
  --color-primary-light: #dbeafe;
  --color-secondary: #10b981;
  --color-secondary-dark: #059669;
}

/* Custom utility classes */
.text-primary {
  color: var(--color-primary);
}

.bg-primary {
  background-color: var(--color-primary);
}

.bg-primary-light {
  background-color: var(--color-primary-light);
}

.bg-primary-dark {
  background-color: var(--color-primary-dark);
}

.text-secondary {
  color: var(--color-secondary);
}

.bg-secondary {
  background-color: var(--color-secondary);
}

.bg-secondary-dark {
  background-color: var(--color-secondary-dark);
}

/* Animations */
.animate-fadeIn {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* List transitions */
.list-enter-active,
.list-leave-active {
  transition: all 0.5s ease;
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateY(30px);
}

/* Ensure proper spacing between list items during transitions */
.list-move {
  transition: transform 0.5s;
}
</style>