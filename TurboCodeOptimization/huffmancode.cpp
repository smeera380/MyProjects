#include"huffmancode.h"

using namespace std;
using std::fixed;
using std::setprecision;


/*--------------------Global variables----------------------------------------*/
string text;                                 /*original file*/
string codes;
string  decoded_codes;
vector<node> code;	                          /*encoded file*/
vector<node> result;
extern vector<int> locations_of_erasure;
extern vector<node> final_result;
/*---------------------------------------------------------------
* Copyright NOV 2010 CSE@TAMU
* All rights reserved.
*
* huffmancode.cpp
*
* This script implements the functions used in turbo coding and decoding.
*
* Version: 1.0
* Programmed By Qing(Tsing) Li
* Last updated date: Nov 2010
---------------------------------------------------------------*/

/*======================================================
FUNCTION: void generate_code()
DESCRIPTION: generating huffman codes for the input text file.
	INPUT:  none
	OUTPUT: The characters and corresponding codes are stored at the result.
RETURN VALUE
    None
======================================================*/

void generate_code()
{

    cout<<"Inside generate code\n";
    priority_queue< node,vector<node>,greater<node> > que;
    /*Use priority_queue to construct Huffman code. This structure
    // creates a tree like structure starting with least number of binary codes for the most frequently occurring character. */
	int i;
	string pathName ;
	string line;


	//cout<<"Please input the text address"<<endl;

	ifstream in( "C:\\Users\\Sumithra\\Documents\\USA\\UFL\\Courses\\WiComm\\Project\\CodeaArtefacts\\TurboCode\\code.txt",ios::in);
    //load the text.

    if (in.is_open())
    {
      while ( getline (in,line) )
      {
        text = text + line;
       }
       in.close();
     }

	for( i=0; i<text.length(); i++ )                           //store all appearing character and accounting the frequency.
	{
		int sub=findChar(text[i]);                            //look up this code appearing or not
		if( sub == -1 )
		{
			node p;                                           //if not, add a new node
            p.times = 1;
			p.c = text[i];
			p.code = "";
            p.child1 = NULL;
            p.child2 = NULL;
            code.push_back(p);
		}
		else
		{
			code[sub].times++;                                //if so, times ++
		}
	}

	while( que.size() > 0 )
            que.pop();

        for( i = 0;i < code.size();i++ )                   //Initiate the priory queue.
			que.push( code[i] );


        node *t1,*t2,*t3;
        while( que.size() >= 2 )                           //generating the tree
        {
            t1 = new node;
            t2 = new node;

            *t1 = que.top();                               //pop out two least frequent nodes.
            que.pop();

            *t2 = que.top();
            que.pop();

            t3 = new node;
			t3->c = '~';
            t3->times = t1->times + t2->times;
            t3->child1 = t1;
            t3->child2 = t2;
            que.push( *t3 );                                //regenerate a new node.

        }

		node root = que.top();                              //the root.
		que.pop();

		queue<node*> queue;
		queue.push(&root);

		while( !queue.empty() )                              //begin encode, BFS
		{
			node *temp=queue.front();
			queue.pop();
			if( temp->child1!=NULL )
			{
				temp->child1->code=temp->code+"0";           //left one,code connects'0'
				queue.push(temp->child1);
			}
			if( temp->child2!=NULL )
			{
				temp->child2->code=temp->code+"1";           //right one£¬code connects'1'
				queue.push(temp->child2);
			}
			if( temp->child1==NULL && temp->child2==NULL )
			{
				result.push_back(*temp);
			}
		}
    cout << "Exiting Generate code";

    return ;

}
/*-----------------------------------------------------
FUNCTION: int findChar( char c )
DESCRIPTION: find character c appearing or not
	INPUT:  character c
	OUTPUT:  if appearing   return the corresponding location.
	         otherwise, return the invalid location -1
RETURN VALUE

		NONE
------------------------------------------------------*/
int findChar( char c )
{
	for( int i=0; i < code.size(); i++ )
	{
		if( code[i].c == c )
			return i;
	}
	return -1;
}


/*-----------------------------------------------------
FUNCTION: void encode()
DESCRIPTION  Huffman code function
	INTPUT:  Global parameter text

	OUTPUT:   Results are stored at code.txt
RETURN VALUE
			NONE.
-----------------------------------------------------*/
void encode()
{
	int i, j;
	generate_code(); /* core Huffman logic*/


	ofstream output;
	output.open( "encoded.txt");

	for( i=0; i<text.length(); i++ )
	{
		for( j=0; j<result.size(); j++ )
		{
			if( result[j].c == text[i] )                      /*look up the corresponding code*/
			{
				codes+=result[j].code;
				break;
			}
		}

	}
    output<<codes;  /* Writes the encoded codes into the file.*/

    cout <<" \n ----------- Huffman encoding results!-------------- \n";
    int resultSize = result.size();
    for(i=0;i<resultSize;i++){
      cout<<result[i].code << " : "<<result[i].c <<"\n";
    }

    final_result = result;
     for(i=0;i<resultSize;i++){
      cout<<final_result[i].code << " : "<<final_result[i].c <<"\n";
    }
}

/*---------------------------------------------------------------
FUNCTION£º void decode( string textName )
DESCRIPTION£º huffman decoding function.
	INPUT: None.

	OUTPUT: the decoded text file
RETURN VALUE
----------------------------------------------------------------*/
void decode( )
{
	int i,j=0, length = 0;
	int p=0;
	string ch;
	bool flag = false;
	string temp;
    string line;
    string deccodes;


	ofstream output;
	output.open( "decoded.txt");


    ifstream in( "turbodecode.txt",ios::in);
    //load the text.


    if (in.is_open())
    {
      while ( getline (in,line) )
      {
        deccodes = deccodes + line;
       }
       in.close();
     }

    cout<<" \n Inside Huffman : decoded_codes :\n";
    cout<<deccodes;

	//decoded_codes="01000110101111000110101110001111011101000111001001";

	temp = deccodes[j];
	cout<<" Temp : " << temp << " Decoded codes length : "<<deccodes.length()<<"\n";

    cout<< " \n Results DS  : "<<"\n";

    //for(p=0;p<resultSize;p++){
     // cout<<result[p].code << " : "<<result[p].c <<"\n";
    //}

	while( j < deccodes.length() )
	{

		for( i=0; i<final_result.size(); i++ )
		{                                                   /*looking for corresponding code*/
			if( final_result[i].code==temp )
			{
				ch +=final_result[i].c;
				cout<<"%%%%%%    : "<<final_result[i].code <<"\n";
				flag=true;
				length ++;
				break;
			}
			//cout<<" No match : "<<result[i].code<<"\n";
		}

		if( flag ) /* found one matching keyword, now reset the temp*/
		{
			temp="";
			j++;
			temp = deccodes[j];
	    	flag=false;
		}
		else /* current set of character[s] does not match a keyword, so keep appending till we find one*/
		{   j++;
			temp += deccodes[j];
		}
	}
	if(!flag)
	{
		//cout<<endl<<" Sorry! We can not restore it completely."<<endl;
		cout<<endl<<" The decoded file has been stored in decoded.txt:"<<endl;
		output<<ch;
		return ;
	}
	else
	{
    	//output<<ch;
		cout<<ch;
		ch.~string();
	}
	cout<<"Final ch : " << ch <<"\n";
	output<<ch;
    output<<endl<<"========================================================="<<endl;
	output.close();
}
