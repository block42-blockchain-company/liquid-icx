import {Component, Vue } from "vue-property-decorator";
import IconService from 'icon-sdk-js'
import store from '../store/index'

@Component({
    components: {
        IconService
    }
})

export class IconMixin extends Vue {
    public readonly provider = new IconService.HttpProvider('https://bicon.net.solidwallet.io/api/v3');
    public readonly iconService = new IconService(this.provider);

    created(){
        window.addEventListener('ICONEX_RELAY_RESPONSE', this.eventHandler)
    }

    eventHandler( e: any) {
        const {type, payload} = e.detail;
        store.getters.isDev && console.log(type, " : ", payload)
        if( type == "RESPONSE_HAS_ACCOUNT"){
            if( payload ) this.hasAddress()
            else alert("No Acccount")
        }
        else if ( type == "RESPONSE_HAS_ADDRESS" ){
            if( payload ) this.requestAddress()
            else alert("No Address")
        }
        else if( type == "RESPONSE_ADDRESS" ){
            store.commit('setWallet', payload)
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