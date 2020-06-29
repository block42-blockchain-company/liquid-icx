<template>
    <div class="navigation-wrapper">
        <img class="background-shape"  src="../../assets/bg-shape.svg"/>
        <div class="navigation">
            <b-navbar toggleable="lg">
                <!-- Left aligned nav items -->
                <b-navbar-brand class="ml-5">
                    <img class="licx-logo" src="../../assets/LICX-logo.svg" alt="logo"/>
                </b-navbar-brand>
                <!-- Right aligned nav items -->
                <IconWallet></IconWallet>
                <router-link to="/about">About</router-link> <!-- Should be in a footer -->
            </b-navbar>
        </div>
    </div>
</template>


<style lang="sccs" scoped src="./header.scss"></style>
<script lang="ts" src="./header.ts"></script>
