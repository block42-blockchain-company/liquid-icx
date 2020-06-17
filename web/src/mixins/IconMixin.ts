import {Component, Vue } from "vue-property-decorator";
import IconService, { IconBuilder } from 'icon-sdk-js'


@Component({
    components: {
    }
})

export class IconMixin extends Vue {
    public readonly provider = new IconService.HttpProvider('https://bicon.net.solidwallet.io/api/v3');
    public readonly iconService = new IconService(this.provider);
    public readonly licx_score_address = "cx4322ccf1ad0578a8909a162b9154170859c913eb"

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

    buildTransaction(_: Record<string, any>){
        const { CallBuilder } = IconBuilder;

        let tx = null;
        if(!_.write){
            tx = new CallBuilder()
                .to(this.licx_score_address)
                .method(_.method)
                .params(_.params)
                .build()
        }
        return tx
    }
}
