/*---------------------------------------------------------------
* Copyright NOV 2010 CSE@TAMU
* All rights reserved.
*
* main.cpp
*
* This script implements the functions used in turbo coding and decoding.
*
* Version: 1.0
* Programmed By Qing(Tsing) Li
* Last updated date: Nov 2010
---------------------------------------------------------------*/
#include <stdlib.h>
#include <stdio.h>
#include<iostream>
#include <math.h>
#include <time.h>
#include<iomanip>
#include<cstdio>
#include<memory>
#include <fstream>
#include<cstring>
#include<queue>
#include<string>
#include<vector>

#include "turbo_code_Log_MAP.h"
//#include "other_functions.h"
#include "huffmancode.h"

int  FRAME_LENGTH;
extern float rate_coding;
extern  TURBO_G turbo_g;
extern int *mx_puncture_turbo;
extern string text;                                 /*original file*/
extern string codes;                                /*encoded file*/
extern vector<node> code;
extern vector<node> result;
vector<node> final_result;
extern int M_num_reg;
extern float *LLR_all_turbo;
extern int *reverse_index_randomintlvr;

/*---------------------------------------------------------------
FUNCTION:
	void gen_source(int *data, int length)

DESCRIPTION:
	This function generate the source bits for simulation.
PARAMETERS:
	INPUT:
		length - Length of needed data.
	OUTPUT:
		data - Contains pointer to source data sequence.
RETURN VALUE:
	None
---------------------------------------------------------------*/
void gen_source(int *data, int length)
{
	int i;

	for (i=0; i<length; i++)
		*(data+i) = (int)codes[i] - 48;
}

/*-----------------------------------------
* FUNCTION: mgrns(double mean,double sigma,double seed,int n,double *a)
* DESCRIPTION:
*	INPUT   mean
*           sigma
*			seed: a random seat
*  OUTPUT
*           a£º Gaussian sequence of length n
*
*  RETURN VALUE
*           NONE
*------------------------------------------*/
void mgrns(double mean,double sigma,double seed,int n,double *a)
{
	int i,k,m;
    double s,w,v,t;
    s=65536.0; w=2053.0; v=13849.0;
    for (k=0; k<=n-1; k++)
	{
		t=0.0;
		for (i=1; i<=12; i++)
        {
			seed=seed*w+v; m=(int)(seed/s);
            seed=seed-m*s; t=t+(seed)/s;
        }/*According to the theory we learn in mathematical course*/
        *(a+k)=mean+sigma*(t-6.0);
    }
    return;
}



/*---------------------------------------------------------------
FUNCTION:
	void AWGN(int *send, float *r, float sigma, int totallength)

DESCRIPTION:
	This function simulate a AWGN channel.
PARAMETERS:
	INPUT:
		send - Input bit sequence need to add noise.
		sigma - Standard deviation of AWGN noise
		totallength - Length of "send".
	OUTPUT:
		r - Contains pointer to the data sequence added with gaussian white noise.
RETURN VALUE:
	None
---------------------------------------------------------------*/
void AWGN(float *send, float *r, float sigma, int totallength)
{
	int i;

	double *noise = (double *)malloc(sizeof(double)*totallength);

	/*
	cout<<"############ Noise ############\n";
	for(i=0;i<sizeof(double)*totallength;i++){
        cout<<*(noise+i);
	}
	*/

	srand((int)time(0));

	double seed =  3.0 - (double)random(100)/100;

	mgrns(0,sigma,seed,totallength,noise);

	for(i=0; i<totallength; i++)
	{
		*(r+i) = (float)( *(send+i) + *(noise+i) );
	}
	//ofstream output( "code.txt", ios::out );
	//output<<r;
	//output.close();
	free(noise);
}



int main(){

    /* Compressing the data using Huffman encoding*/
    encode();

    FRAME_LENGTH = codes.length(); // this would contain the compressed, Huffman coded bits

    /* TURBO ENCODING */
   	int			*trafficflow_source = NULL,traffic_source_length, *trafficflow_decoded = NULL, err_bit_num_traffic[8],i, j, ien,total;
	float		*coded_trafficflow_source = NULL,*trafficflow_for_decode = NULL,EbN0dB = 0,en, sgma,err_bit_rate_traffic[8], max_LLR = 0.0;

	double Eb_N0_dB[8] = {2.8,2.8,2.8,2.8,2.8,2.8,2.8,2.8};

	int codedlength = 2*FRAME_LENGTH*sizeof(float);

	clock_t start, endtime;

	trafficflow_source=(int *)malloc(FRAME_LENGTH*sizeof(int));	//systematic data length
	coded_trafficflow_source=(float *)malloc(2*FRAME_LENGTH*sizeof(float)); //systematic data + parity
	trafficflow_for_decode=(float *)malloc(2*FRAME_LENGTH*sizeof(float));//coded data at the receiving end
	trafficflow_decoded=(int *)malloc(FRAME_LENGTH*sizeof(int));//data after decoding
	traffic_source_length = FRAME_LENGTH; //source data length

    /* Initialize the parameters for Turbo encoding */
    TurboCodingInit(traffic_source_length);

    		/*====   output the simulation parameters to screen======*/
    printf("\n======================== Turbo code simulation :========================\n");
	printf("\n Some parameters are as follows: \n");
	printf("\nlog map decoder\n");
	printf("frame length : %d \n", traffic_source_length);
	printf("generators g = \n");

	for (i=0; i<turbo_g.N_num_row; i++)
	{
	  for (j=0; j<turbo_g.K_num_col; j++)
      {
		printf(" %d  ", *(turbo_g.g_matrix+i*turbo_g.K_num_col+j));
      }
      printf("\n");
    }
    //TO BE REMOVED
    ien=0;
    /* Printing the SNR */
    //for (ien=0; ien<8; ien++)  // for the Simulations
	//{
		total = 0;

		printf("\n /*---------------------------------------------*/\n");
		printf("\n Simulation %d \n", ien + 1);

		EbN0dB = (float)Eb_N0_dB[ien];

		en = (float)pow(10,(EbN0dB)/10);

		sgma = (float)(1.0/sqrt(2*rate_coding*en));

		err_bit_num_traffic[ien] = 0;

		err_bit_rate_traffic[ien] = 0.0;


		printf("\n Eb/N0 = %f \n", EbN0dB);

		if (TURBO_PUNCTURE)
     		printf(" punctured to rate 1/2\n");
		else
		    printf(" unpunctured\n");


		printf(" Number of iterations: %d \n", N_ITERATION);

		if (TURBO_PUNCTURE)
			printf( "\n punctured to rate 1/2\n");
		else
			printf( "\n unpunctured\n");

		/* Turbo Encoding commencing */
		start=clock();/*staring time*/
		cout << "Starting time : " << start <<"\n";

        traffic_source_length = FRAME_LENGTH;

		gen_source(trafficflow_source, traffic_source_length);

        cout << "Printing the generated traffic flow source \n";

        for (i=0; i< traffic_source_length ; i++){
            cout << *(trafficflow_source+i) << "  ";

        }
        cout <<"\n";

        //-----------------------------------------------------------
		/* Turbo Encoding */
		cout << "Commencing Turbo encoding \n";
		TurboCodingTraffic(trafficflow_source, coded_trafficflow_source, &traffic_source_length);

		cout<<"\n Turbo Coded data \n";
		for(i=0;i<codedlength;i++){
            cout << *(coded_trafficflow_source+i) <<"    ";
		}

		cout<<"\n \nTurbo Encoding complete \n";

		//------------------------------------------------------------
		/* Adding AWGN Noise to corrupt the data */

        AWGN(coded_trafficflow_source, trafficflow_for_decode, sgma,traffic_source_length);

        cout<<"\n Coded data after adding Noise    :  Coded data length  :  "<< codedlength << "  \n";
        for(i=0;i<codedlength;i++){
            cout << *(trafficflow_for_decode+i) <<"    ";
		}

		//-----------------------------------------------------------
        cout<<"\n \n Commencing Turbo Decode \n";
        cout <<"@@@@"<< traffic_source_length<<"\n";

        /* Turbo decoding */
        TurboDecodingTraffic(trafficflow_for_decode, trafficflow_decoded, &traffic_source_length, EbN0dB);
        //TurboDecodingTraffic(float *trafficflow_for_decode, int *trafficflow_decoded,int *trafficflow_length, float EbN0dB)


        cout<<"\n Turbo Decoding complete \n";
        //int resultSize = result.size();
        for(int p=0;p<final_result.size();p++){
            cout<<final_result[p].code << " : "<<final_result[p].c <<"\n";
        }



        /*
		for (i=0; i< traffic_source_length ; i++)
		{
			if (*(trafficflow_source+i) != *(trafficflow_decoded+i))
			{
				err_bit_num_traffic[ien] = err_bit_num_traffic[ien]+1;
				printf("LLR[%d] =  %f\n\n",*(reverse_index_randomintlvr + i), *(LLR_all_turbo + *(reverse_index_randomintlvr + i) ));
				if(fabs(*(LLR_all_turbo + *(reverse_index_randomintlvr + i) )) > max_LLR)
						max_LLR = fabs(*(LLR_all_turbo + *(reverse_index_randomintlvr + i)));
			}
			else
			{
				printf("LLR[%d] =  %f\n\n",*(reverse_index_randomintlvr + i), *(LLR_all_turbo + *(reverse_index_randomintlvr + i) ));

			}
		}


		for (i=0; i< traffic_source_length ; i++)
		{
			if (*(trafficflow_source+i) == *(trafficflow_decoded+i)&&fabs(*(LLR_all_turbo +*(reverse_index_randomintlvr + i))) < max_LLR)
			{
				total ++;
			}
		}

		float wrong = (float) total/(float) traffic_source_length;
		err_bit_rate_traffic[ien] = (float)err_bit_num_traffic[ien]/(traffic_source_length) ;
		printf("\n The Error bit probability is %f  \n",err_bit_rate_traffic[ien]);
		printf("\n The Error bit probability is %f \n",err_bit_rate_traffic[ien]);
		printf("maxmum LLR of error bit is %f and SNR is %f \n\n", max_LLR,EbN0dB);
		printf("Among correct bits, there are %f % of them whose LLR less than max_LLR\n", wrong);
		printf("===========================================================================\n\n");
		printf("===========================================================================\n\n");
        */

        decode();

        endtime=clock();
        double totalTime = double(endtime - start)/CLOCKS_PER_SEC;
	    cout<< "%Total time taken : "<<totalTime;
        cout<<"\n";

	    printf("The corresponding LLR of error bits for simulation %d :\n\n", ien + 1);
        free(LLR_all_turbo);
	//}
   return 0;
}
