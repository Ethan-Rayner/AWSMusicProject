package com.amazonaws.samples;
import java.io.File;
import java.io.IOException;
import java.net.URL;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Iterator;

import com.amazonaws.regions.Regions;
import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.AmazonS3ClientBuilder;
import com.amazonaws.services.s3.model.PutObjectRequest;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;



public class ImagesToS3 {
	
	private static final String bucketName = "assignment1-music";
	private static final Regions clientRegion = Regions.US_EAST_1;
	
	public static void main(String[] args) throws Exception {
		//start
		JsonParser parser = new JsonFactory().createParser(new File("a1.json"));     
        JsonNode rootNode = new ObjectMapper().readTree(parser);
        Iterator<JsonNode> iter = rootNode.iterator();
        ArrayNode currentNode;

        AmazonS3 s3Client = AmazonS3ClientBuilder.standard()
                .withRegion(clientRegion)
                .build();
        
        while (iter.hasNext()) {
            currentNode = (ArrayNode) iter.next();
            Iterator<JsonNode> innerIter = currentNode.iterator();

            while(innerIter.hasNext()) {
                JsonNode node = innerIter.next();
                String imageURL = node.path("img_url").asText();
                
                String fileName = downloadImage(imageURL, s3Client);
                
                if (!fileName.equals("Exists")) {
                s3Client.putObject(new PutObjectRequest(bucketName, fileName, new File(fileName)));
                new File(fileName).delete();
                }
                
            }
        }
        System.out.println("Completed");
        parser.close();

	}
	
	
	private static String downloadImage(String imageUrl, AmazonS3 s3Client) throws IOException {
		//downloads and saves images to local pc
		String fileName = imageUrl.substring(imageUrl.lastIndexOf("/") + 1);
		//checks whether image already exists in database
		if (s3Client.doesObjectExist(bucketName, fileName) || Files.exists(Paths.get(fileName))){
	        return "Exists";
		}
		else {
			Files.copy(new URL(imageUrl).openStream(), Paths.get(fileName));
	        return fileName;
		}
		}
	}


