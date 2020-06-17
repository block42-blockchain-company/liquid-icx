<template>
    <div class="swap">
        <b-tabs justified>
            <b-tab :title-item-class="'tab-item'"
                   :title-link-class="'tab-title'"
                   v-for="(key, value) in pairs"
                   v-bind:key="'tab-' + key"
                   :title="key + ' -> ' + value" :active="(key === 'ICX')">
                <b-form class="mt-5 swap-form container-fluid">
                    <div class="row mb-5">
                        <div class="col-sm-6">
                            <b-form-input class="amount-input"
                                          type="number"
                                          v-model="amount"
                                          :placeholder="'Amount ' + key"/>
                        </div>
                        <div class="col-sm-6">
                            <div class="amount-mirror mt-2">
                                {{ (amount === "") ? "Amount " + value : amount + " " +value }}
                            </div>
                        </div>
                    </div>
                    <b-button :disabled="((wallet == null) || (amount === ''))"
                              class="btn-convert mb-4"
                              @click="join" variant="primary">Convert</b-button>
                </b-form>
            </b-tab>
        </b-tabs>
    </div>
</template>

<style lang="sccs" src="./swap.scss"></style>
<script lang="ts" src="./swap.ts"></script>