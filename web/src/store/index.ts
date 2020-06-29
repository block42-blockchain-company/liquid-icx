import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    dev : true,
    attachedIconexListner: false,
    wallet : null,
  },
  getters : {
    isDev : state => {
      return  state.dev;
    },
    isListening : state => {
      return state.attachedIconexListner
    },
    getWallet : state => {
      return state.wallet
    }
  },
  mutations: {
    setWallet( state, wallet ) {
      state.wallet = wallet
    },
    startListening : state => {
      state.attachedIconexListner = true
    }
  },
  actions: {},
  modules: {}
})
