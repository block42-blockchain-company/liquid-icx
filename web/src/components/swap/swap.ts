import { Vue, Component } from 'vue-property-decorator'


@Component({
    components: {
    }
})
export default class Swap extends Vue
{
    readonly pairs = {"LICX": "ICX",
                       "ICX": "LICX"}

    amount= ""

}