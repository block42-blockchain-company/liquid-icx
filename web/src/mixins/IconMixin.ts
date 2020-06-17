import {Component, Vue } from "vue-property-decorator";
import IconService, { IconBuilder, IconValidator } from 'icon-sdk-js'


@Component({
    components: {
    }
})

export class IconMixin extends Vue {
    public readonly provider = new IconService.HttpProvider('https://bicon.net.solidwallet.io/api/v3');
    public readonly iconService = new IconService(this.provider);
    public readonly licx_score_address = "cxbf9095b8b711068cc5cd1f813b60647e0325408d"

    async getBalances(address ){
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

    async getLicxApi(){
        const apiList = await this.iconService.getScoreApi(this.licx_score_address).execute();
        return apiList.getList()
    }

    checkAddress( address: string){
        return IconValidator.isEoaAddress(address)
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
}
