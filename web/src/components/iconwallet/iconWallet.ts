import { Mixins, Component } from 'vue-property-decorator'
import {mapGetters, mapMutations} from "vuex";
import store from "@/store";
import {IconMixin} from "@/mixins/IconMixin";

@Component({
    computed: mapGetters({ wallet : 'getWallet'}),
    methods: mapMutations({ setWallet : 'setWallet' })
})
export default class IconWallet extends Mixins(IconMixin)
{
    created(){
        window.addEventListener('ICONEX_RELAY_RESPONSE', this.eventHandler)
    }

    eventHandler( e: any) {
        const {type, payload} = e.detail;
        store.getters.isDev && console.log(type, " : ", payload)
        if( type == "RESPONSE_HAS_ACCOUNT"){
            if( payload ) this.hasAddress()
            else alert("No Acccount") // TODO we need to find a better way to infrm user
        }
        else if ( type == "RESPONSE_HAS_ADDRESS" ){
            if( payload ) this.requestAddress()
            else alert("No Address")
        }
        else if( type == "RESPONSE_ADDRESS" ){
            this.getBalances(payload).then(result => {
                store.getters.isDev && console.log("Balances: ", result)
                store.commit('setWallet', {
                    address: payload,
                    balances: result,
                })
            })
        }
    }

    hasAccount(){
        this.dispatchEvent("REQUEST_HAS_ACCOUNT", null)
    }

    hasAddress(){
        this.dispatchEvent("REQUEST_HAS_ADDRESS", null)
    }

    requestAddress(){
        this.dispatchEvent("REQUEST_ADDRESS", null)
    }

    dispatchEvent(type_: string, payload_: any){
        const customEvent = new CustomEvent('ICONEX_RELAY_REQUEST', {detail: {
                type: type_,
                payload: payload_
            }});
        window.dispatchEvent(customEvent);
    }
}