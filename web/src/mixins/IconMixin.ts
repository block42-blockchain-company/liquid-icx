import {Component, Vue } from "vue-property-decorator";
import IconService, { IconBuilder, IconValidator } from 'icon-sdk-js'
import store from "@/store";
import {mapGetters, mapMutations} from "vuex";
import logger from "vuex/dist/logger";


@Component({
    computed: mapGetters({
        dev: "isDev",
        wallet : 'getWallet',
        attachedListener: "isListening"
    }),
    methods: mapMutations({ setWallet : 'setWallet' })
})

export class IconMixin extends Vue {
    public readonly provider = new IconService.HttpProvider('https://bicon.net.solidwallet.io/api/v3');
    public readonly iconService = new IconService(this.provider);
    public readonly licx_score_address = "cxbf9095b8b711068cc5cd1f813b60647e0325408d"

    dev!: boolean
    attachedListener!: boolean

    /*
    * ------------------ICONEX METHODS--------------------
    * https://www.icondev.io/docs/chrome-extension-connect
    * ----------------------------------------------------
    * */
    created(){
        if (!this.attachedListener){
            window.addEventListener('ICONEX_RELAY_RESPONSE', this.iconexEventHandler)
            store.commit("startListening", null)
        }
    }

    iconexEventHandler( e: any) {
        const {type, payload} = e.detail;
        this.dev && console.log(type, " : ", payload)
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
        else if( type === "RESPONSE_JSON-RPC") {
            this.getTxResult(payload.result)
        }
    }

    hasAccount(){
        this.dispatchIconexEvent("REQUEST_HAS_ACCOUNT", null)
    }

    hasAddress(){
        this.dispatchIconexEvent("REQUEST_HAS_ADDRESS", null)
    }

    requestAddress(){
        this.dispatchIconexEvent("REQUEST_ADDRESS", null)
    }

    dispatchIconexEvent(type_: string, payload_: any){
        const customEvent = new CustomEvent('ICONEX_RELAY_REQUEST', {
            detail: {
                type: type_,
                payload: payload_
            }});
        window.dispatchEvent(customEvent);
    }


    buildTransaction(_: Record<string, any>){
        const { CallBuilder, CallTransactionBuilder } = IconBuilder;

        let tx = null;
        if(!_.write){
            tx = new CallBuilder()
                .to(this.licx_score_address)
                .method(_.method)
                .params(_.params)
                .build()
        }
        else{
            tx = new CallTransactionBuilder()
                .from(_.from)
                .to(this.licx_score_address)
                .value(_.value)
                .nid(3)
                .stepLimit(_.steps)
                .version(BigInt(3))
                .timestamp((new Date()).getTime() * 1000)
                .nonce(100)
                .method(_.method)
                .params(_.params)
                .build()
        }
        return tx
    }

    async getTxResult(hash: string) {
        return await this.iconService.getTransactionResult(hash).execute().then(res => {
            console.log(res)
        }).catch(err => {
            if(err.includes("Pending transaction"))
                setTimeout(this.getTxResult.bind(null, hash), 2000)
            else
                console.error(err)
        })
    }

    checkAddress( address: string){
        return IconValidator.isEoaAddress(address)
    }

    async getBalances(address){
        const icxBalance = await this.iconService.getBalance(address).execute();
        const licxBalance = await this.iconService.call(this.buildTransaction({
            write: false,
            method: "balanceOf",
            params: {_owner: address}
        })).execute()

        return {
            icx: BigInt(icxBalance["c"].join('')),
            licx: BigInt(licxBalance)
        }
    }
}
