<template>
    <div class="transfer">
        <h3>Transfer <span>LICX</span></h3>
        <b-form class="transfer-form mt-4">
            <b-input class="address input-licx" placeholder="Enter reciever's address"></b-input>
            <b-input class="amount input-licx" type="number" placeholder="Enter sum you want to transfer"></b-input>
            <b-button class="btn-transfer btn-licx mt-3">Transfer</b-button>
        </b-form>
    </div>
</template>

<style lang="sccs" src="./transfer.scss"></style>
<script lang="ts" src="./transfer.ts"></script>