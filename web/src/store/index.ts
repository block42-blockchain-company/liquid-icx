import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    dev : true,
    wallet : null
  },
  getters : {
    isDev : state => {
      return  state.dev;
    },
    getWallet : state => {
      return state.wallet
    }
  },
  mutations: {
    setWallet( state, wallet ) {
      state.wallet = wallet
    }
  },
  actions: {
  },
  modules: {
  }
})