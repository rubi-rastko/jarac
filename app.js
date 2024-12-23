import { IWBServer as IWBApp } from "wbserver/iwbserver";

const app = new IWBApp( "./arkived" );
app.loadDiskConfig( );
app.start();
